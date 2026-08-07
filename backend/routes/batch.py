from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import uuid
import json
import os
from datetime import datetime
import logging

from models.batch import BatchCreate, BatchResponse, StageExecutionRequest, StageExecutionResponse, BatchStatus
from services.script_executor import ScriptExecutor
from services.claude_service import ClaudeService
from config import settings

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for batches (in production, use a database)
batches: Dict[str, Dict[str, Any]] = {}

# Initialize script executor
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
logger.info(f"Scripts directory: {scripts_dir}")
logger.info(f"Config directory: {settings.config_dir}")
logger.info(f"Upload directory: {settings.upload_dir}")
logger.info(f"Log directory: {settings.log_dir}")
executor = ScriptExecutor(
    scripts_dir=scripts_dir,
    config_dir=settings.config_dir,
    upload_dir=settings.upload_dir,
    log_dir=settings.log_dir
)

def preprocess_excel_to_csv(excel_file: str) -> Dict[str, str]:
    """Convert uploaded Excel file to required CSV format"""
    if not PANDAS_AVAILABLE:
        raise HTTPException(status_code=400, detail="pandas is required for Excel preprocessing")
    
    try:
        # Read Excel with header=1 to skip the first row which contains headers
        df = pd.read_excel(excel_file, header=1)
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Add row_id column (required by the script)
        df.insert(0, 'row_id', range(1, len(df) + 1))
        
        # Map Excel columns to script expected columns
        # Note: In this Excel file, column 13 contains destination names, column 12 has duration info
        column_mapping = {
            'Unnamed: 0': 'name',
            'Unnamed: 1': 'variant_name',
            'Unnamed: 2': 'name_backend',
            'Unnamed: 3': 'activity_link',
            'Unnamed: 4': 'slug',
            'Unnamed: 13': 'location',  # Destination names are in column 13
            'Unnamed: 12': 'duration',  # Duration info is in column 12
            'Unnamed: 14': 'day_description',
            'Unnamed: 15': 'customer_notes',
            'Unnamed: 16': 'breakfast_included',
            'Unnamed: 17': 'lunch',
            'Unnamed: 18': 'dinner',
            'Unnamed: 19': 'priced_in_transfer',
            'Unnamed: 20': 'ticket_inclusion'
        }
        
        # Rename columns that exist in the mapping
        df = df.rename(columns=column_mapping)
        
        # Fix: swap location and duration if they're in wrong columns
        if 'location' in df.columns and 'duration' in df.columns:
            # Check if duration column contains destination names
            sample_duration = df['duration'].dropna().iloc[0] if len(df['duration'].dropna()) > 0 else None
            if sample_duration and isinstance(sample_duration, str):
                # If duration looks like a destination name (e.g., "Cochin", "Munnar"), move it to location
                known_destinations = ['Cochin', 'Munnar', 'Thekkady', 'Alleppey', 'Varkala', 'Kovalam', 'Kanniyakumari', 'Rameshwaram', 'Madurai', 'Vagamon', 'Kumarakom']
                if any(dest.lower() in sample_duration.lower() for dest in known_destinations):
                    print(f"Detected destination names in duration column, swapping with location")
                    df['location'] = df['duration']
                    df['duration'] = None  # Clear duration as it actually contained destinations
        
        # Rename columns that exist in the mapping
        df = df.rename(columns=column_mapping)
        
        # Filter out rows without product names
        df = df[df['name'].notna() & (df['name'] != '')]
        
        # Reset row_id after filtering
        df['row_id'] = range(1, len(df) + 1)
        
        # Prepare products CSV with required columns
        products_csv = os.path.join(settings.upload_dir, "products_from_sheet.csv")
        products_df = df[['row_id', 'name', 'location', 'duration', 'day_description']].copy()
        products_df.to_csv(products_csv, index=False)
        
        # Create variants CSV from the same data
        variants_new_csv = os.path.join(settings.upload_dir, "variants_new_products.csv")
        variants_df = df[['row_id', 'variant_name']].copy()
        variants_df.columns = ['product_row_id', 'variant_name']
        variants_df['booking_type'] = 'group'
        variants_df['inventory_type'] = 'pax'
        variants_df['min_passengers'] = 1
        variants_df['transfer_inclusion'] = 'Not Included'
        variants_df['ticket_inclusion'] = 'Not Ticketed'
        variants_df.to_csv(variants_new_csv, index=False)
        
        # Create empty existing products CSV
        variants_existing_csv = os.path.join(settings.upload_dir, "variants_existing_products.csv")
        pd.DataFrame(columns=["product_id", "variant_name", "booking_type", "inventory_type", "min_passengers", "transfer_inclusion", "ticket_inclusion"]).to_csv(variants_existing_csv, index=False)
        
        return {
            "products_csv": products_csv,
            "variants_new_csv": variants_new_csv,
            "variants_existing_csv": variants_existing_csv
        }
    except Exception as e:
        logger.error(f"Error preprocessing Excel: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Excel preprocessing failed: {str(e)}")

@router.post("/", response_model=BatchResponse)
async def create_batch(batch: BatchCreate):
    """Create a new batch"""
    batch_id = str(uuid.uuid4())
    
    new_batch = {
        "id": batch_id,
        "name": batch.name,
        "description": batch.description,
        "client_id": batch.client_id,
        "source_file": batch.source_file,
        "status": BatchStatus.PENDING,
        "created_at": datetime.now().isoformat(),
        "updated_at": None,
        "results": None,
        "error_message": None
    }
    
    batches[batch_id] = new_batch
    logger.info(f"Created batch {batch_id}: {batch.name}")
    
    return BatchResponse(**new_batch)

@router.get("/", response_model=List[BatchResponse])
async def list_batches():
    """List all batches"""
    return [BatchResponse(**batch) for batch in batches.values()]

@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str):
    """Get a specific batch"""
    if batch_id not in batches:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchResponse(**batches[batch_id])

@router.post("/{batch_id}/execute", response_model=StageExecutionResponse)
async def execute_stage(batch_id: str, request: StageExecutionRequest):
    """Execute a specific stage of the batch workflow"""
    print(f"DEBUG: Received execute_stage request for batch {batch_id}, stage {request.stage}")
    print(f"DEBUG: Available batches: {list(batches.keys())}")
    
    if batch_id not in batches:
        print(f"DEBUG: Batch {batch_id} not found in batches")
        raise HTTPException(status_code=404, detail=f"Batch not found. Available batches: {list(batches.keys())}")
    
    batch = batches[batch_id]
    print(f"DEBUG: Found batch {batch_id} with status {batch.get('status')}")
    print(f"DEBUG: Batch details: {batch}")
    
    # Prepare file paths (use absolute paths)
    config_file = os.path.abspath(os.path.join(settings.config_dir, "batch_config.json"))
    token_file = os.path.abspath(os.path.join(settings.config_dir, "access_token.txt"))
    
    # Auto-create token file from .env if it doesn't exist
    if not os.path.exists(token_file):
        try:
            if settings.thrillo_access_token:
                with open(token_file, "w") as f:
                    f.write(settings.thrillo_access_token.strip())
                logger.info("Created token file from .env")
        except Exception as e:
            logger.warning(f"Could not create token file from .env: {e}")
    
    # Auto-create default config file if it doesn't exist
    if not os.path.exists(config_file):
        try:
            default_config = {
                "base_url": settings.thrillo_base_url,
                "client_id": settings.thrillo_client_id,
                # enrich_batch.py requirements
                "region_name": "Kerala",
                "visibility_scopes": ["public"],
                "open_slots_until": "2026-12-31",
                "required_inclusion_id": "",
                # Destination mappings for Kerala
                "destination_mappings": {
                    "Cochin": {"destination_id": "5191", "destination_name": "Cochin"},
                    "Munnar": {"destination_id": "5210", "destination_name": "Munnar"},
                    "Thekkady": {"destination_id": "7035", "destination_name": "Thekkady"},
                    "Alleppey": {"destination_id": "6879", "destination_name": "Alleppey"},
                    "Varkala": {"destination_id": "6239", "destination_name": "Varkala"},
                    "Kovalam": {"destination_id": "5205", "destination_name": "Kovalam"},
                    "Kanniyakumari": {"destination_id": "6887", "destination_name": "Kanniyakumari"},
                    "Rameshwaram": {"destination_id": "7040", "destination_name": "Rameshwaram"},
                    "Madurai": {"destination_id": "5315", "destination_name": "Madurai"},
                    "Vagamon": {"destination_id": "7042", "destination_name": "Vagamon"},
                    "Kumarakom": {"destination_id": "6955", "destination_name": "Kumarakom"}
                },
                # finalize_batch.py requirements
                "vendor_names": ["Sv Sky Blue Orchids", "Carrot Cruises Shipping P. Ltd", "GUIDELINE TRAVELS HOLIDAYS INDIA PRIVATE LIMITED HOLIDAY DIVISION"],
                "reseller_partner_id": "4",
                "inventory_id": "1",
                "margin": 10,
                "currency": "INR",
                "policy_ids": {
                    "confirmation_policy_id": "20988",
                    "refund_policy_id": "20984",
                    "cancellation_policy_id": "20985",
                    "payment_term_policy_id": "1671"
                },
                "vendor_payment_term_policy_id": "2207",
                "default_variant": {
                    "booking_type": "group",
                    "inventory_type": "pax",
                    "min_passenger_count": 1,
                    "transfer_inclusion": "Not Included",
                    "ticket_inclusion": "Not Ticketed",
                    "availability_sources": ["partner"],
                    "duration_type": "days_hours_minutes",
                    "duration_days": 1,
                    "duration_hours": 0,
                    "duration_minutes": 0
                },
                "booking_settings": {
                    "enable_send_enquiry": True,
                    "is_ticketed": "no",
                    "time_zone": "Asia/Kolkata",
                    "min_percentage_amount_to_confirm": 20
                },
                "seo_template": {
                    "meta_title": "{name} in Kerala",
                    "meta_description": "Experience {name} in Kerala",
                    "og_title": "{name} - Thrillophilia",
                    "og_description": "Book {name} in Kerala"
                },
                "existing_product_activity_overrides": {}
            }
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            logger.info("Created default config file")
        except Exception as e:
            logger.warning(f"Could not create default config file: {e}")
    
    # Verify files exist
    if not os.path.exists(config_file):
        raise HTTPException(status_code=400, detail="Config file not found. Please upload a configuration file.")
    if not os.path.exists(token_file):
        raise HTTPException(status_code=400, detail="Token file not found. Please save your token in the .env file or use the Token Capture page.")
    
    started_at = datetime.now()
    
    try:
        if request.stage == 1:
            # Stage 1: Create products and variants
            # First, preprocess Excel to CSV if source file is Excel
            source_file = batch["source_file"]
            if source_file.endswith(('.xlsx', '.xls')):
                print(f"Preprocessing Excel file: {source_file}")
                csv_files = preprocess_excel_to_csv(os.path.join(settings.upload_dir, source_file))
                products_csv = os.path.abspath(csv_files["products_csv"])
                variants_new_csv = os.path.abspath(csv_files["variants_new_csv"])
                variants_existing_csv = os.path.abspath(csv_files["variants_existing_csv"])
            else:
                products_csv = os.path.abspath(os.path.join(settings.upload_dir, "products_from_sheet.csv"))
                variants_new_csv = os.path.abspath(os.path.join(settings.upload_dir, "variants_new_products.csv"))
                variants_existing_csv = os.path.abspath(os.path.join(settings.upload_dir, "variants_existing_products.csv"))
            
            if not all(os.path.exists(f) for f in [products_csv, variants_new_csv]):
                raise HTTPException(status_code=400, detail="Required CSV files not found")
            
            print(f"Executing Stage 1 with files:")
            print(f"  Config: {config_file}")
            print(f"  Token: {token_file}")
            print(f"  Products CSV: {products_csv}")
            print(f"  Variants New CSV: {variants_new_csv}")
            print(f"  Variants Existing CSV: {variants_existing_csv}")
            print(f"  Dry run: {request.dry_run}")
            
            try:
                result = await executor.execute_stage1(
                    config_file=config_file,
                    token_file=token_file,
                    products_csv=products_csv,
                    variants_new_csv=variants_new_csv,
                    variants_existing_csv=variants_existing_csv,
                    dry_run=request.dry_run
                )
                
                print(f"Stage 1 result: {result}")
                
                if result["success"]:
                    batch["status"] = BatchStatus.STAGE1_COMPLETED
                else:
                    batch["status"] = BatchStatus.FAILED
                    batch["error_message"] = result.get("error", "Stage 1 execution failed")
                    batch["error_message"] += f" - Return code: {result.get('return_code', 'unknown')}"
                    batch["error_message"] += f" - Stderr: {result.get('stderr', '')[:200]}"
            except Exception as e:
                print(f"Exception during Stage 1 execution: {str(e)}")
                batch["status"] = BatchStatus.FAILED
                batch["error_message"] = f"Exception: {str(e)}"
        
        elif request.stage == 2:
            # Stage 2: Enrich batch
            if batch["status"] != BatchStatus.STAGE1_COMPLETED:
                raise HTTPException(status_code=400, detail="Stage 1 must be completed first")
            
            enrichment_plan = os.path.join(settings.upload_dir, "enrichment_plan.json")
            
            # Update enrichment plan with actual product codes from Stage 1 results
            try:
                stage1_results = batch.get("stage1_results", [])
                if stage1_results:
                    print("Updating enrichment plan with actual product codes from Stage 1...")
                    import subprocess
                    stage1_results_file = os.path.join(settings.upload_dir, "stage1_results.json")
                    with open(stage1_results_file, 'w') as f:
                        json.dump({"stage1_results": stage1_results}, f, indent=2)
                    
                    result = subprocess.run([
                        "python", 
                        os.path.join(settings.base_dir, "update_enrichment_plan.py"),
                        stage1_results_file,
                        enrichment_plan
                    ], capture_output=True, text=True)
                    if result.returncode == 0:
                        print("Enrichment plan updated with actual product codes")
                    else:
                        print(f"Warning: Failed to update enrichment plan: {result.stderr}")
            except Exception as e:
                print(f"Warning: Could not update enrichment plan: {str(e)}")
            
            if not os.path.exists(enrichment_plan):
                raise HTTPException(status_code=400, detail="Enrichment plan not found")
            
            # Generate enrichment plan if it doesn't exist or is empty
            try:
                with open(enrichment_plan, 'r') as f:
                    plan_data = json.load(f)
                    if not plan_data.get("products") and not plan_data.get("variants"):
                        # Regenerate enrichment plan from Excel
                        source_file = batch["source_file"]
                        if source_file.endswith(('.xlsx', '.xls')):
                            print("Regenerating enrichment plan from Excel...")
                            import subprocess
                            result = subprocess.run([
                                "python", 
                                os.path.join(settings.base_dir, "generate_enrichment_plan.py"),
                                os.path.join(settings.upload_dir, source_file),
                                enrichment_plan
                            ], capture_output=True, text=True)
                            if result.returncode == 0:
                                print("Enrichment plan regenerated successfully")
                            else:
                                print(f"Warning: Could not regenerate enrichment plan: {result.stderr}")
            except Exception as e:
                print(f"Warning: Could not check enrichment plan: {e}")
            
            result = await executor.execute_stage2(
                config_file=config_file,
                token_file=token_file,
                enrichment_plan=enrichment_plan,
                dry_run=request.dry_run,
                use_ai=True  # Enable AI enrichment by default
            )
            
            if result["success"]:
                batch["status"] = BatchStatus.STAGE2_COMPLETED
                print(f"Stage 2 completed successfully")
            else:
                batch["status"] = BatchStatus.FAILED
                batch["error_message"] = result.get("error", "Stage 2 execution failed")
                batch["error_message"] += f" - Return code: {result.get('return_code', 'unknown')}"
                batch["error_message"] += f" - Stderr: {result.get('stderr', '')[:200]}"
                print(f"Stage 2 failed: {batch['error_message']}")
        
        elif request.stage == 3:
            # Stage 3: Finalize batch
            if batch["status"] != BatchStatus.STAGE2_COMPLETED:
                raise HTTPException(status_code=400, detail="Stage 2 must be completed first")
            
            enrichment_plan = os.path.join(settings.upload_dir, "enrichment_plan.json")
            source_sheet = os.path.join(settings.upload_dir, "products_from_sheet.csv")
            
            if not os.path.exists(enrichment_plan):
                raise HTTPException(status_code=400, detail="Enrichment plan not found")
            if not os.path.exists(source_sheet):
                raise HTTPException(status_code=400, detail="Source sheet not found")
            
            result = await executor.execute_stage3(
                config_file=config_file,
                token_file=token_file,
                enrichment_plan=enrichment_plan,
                source_sheet=source_sheet,
                dry_run=request.dry_run
            )
            
            if result["success"]:
                batch["status"] = BatchStatus.COMPLETED
            else:
                batch["status"] = BatchStatus.FAILED
                batch["error_message"] = result.get("error", "Stage 3 execution failed")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid stage number")
        
        batch["updated_at"] = datetime.now().isoformat()
        batch["results"] = result
        
        completed_at = datetime.now()
        
        return StageExecutionResponse(
            batch_id=batch_id,
            stage=request.stage,
            status="completed" if result["success"] else "failed",
            dry_run=request.dry_run,
            started_at=started_at,
            completed_at=completed_at,
            results=result
        )
        
    except Exception as e:
        logger.error(f"Error executing stage {request.stage} for batch {batch_id}: {str(e)}")
        batch["status"] = BatchStatus.FAILED
        batch["error_message"] = str(e)
        batch["updated_at"] = datetime.now().isoformat()
        
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{batch_id}")
async def delete_batch(batch_id: str):
    """Delete a batch"""
    if batch_id not in batches:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    del batches[batch_id]
    logger.info(f"Deleted batch {batch_id}")
    
    return {"message": "Batch deleted successfully"}