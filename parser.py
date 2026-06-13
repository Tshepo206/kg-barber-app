import os
import psycopg2
from pydantic import BaseModel, Field, field_validator
from datetime import date
from dotenv import load_dotenv

# Initialize cloud database environment connection parameters
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# =====================================================================
# 1. DEFINE THE FINANCIAL VALIDATION GUARDRAILS (PYDANTIC)
# =====================================================================
class FinancialTransaction(BaseModel):
    tx_date: date = Field(default_factory=date.today)
    category: str = Field(description="Must be exactly 'Service', 'Retail', or 'Expense'")
    description: str = Field(description="Brief narrative of the item or action")
    amount: float = Field(description="The numeric currency value in Rands")
    payment_method: str = Field(description="Must be exactly 'Cash' or 'Card'")

    @field_validator('category')
    def validate_category(cls, v):
        if v not in ['Service', 'Retail', 'Expense']:
            raise ValueError("Category must be Service, Retail, or Expense")
        return v

    @field_validator('payment_method')
    def validate_payment_method(cls, v):
        if v not in ['Cash', 'Card']:
            raise ValueError("Payment method must be Cash or Card")
        return v

# =====================================================================
# 2. DEFINE THE CLOUD DATA INGESTION SUITE (POSTGRESQL)
# =====================================================================
def log_transaction_to_db(tx: FinancialTransaction):
    """Safely executes an INSERT transaction into the Render Postgres instance."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO financial_ledger (date, category, description, amount, payment_method)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(query, (tx.tx_date, tx.category, tx.description, tx.amount, tx.payment_method))
        conn.commit()
        print(f"✅ Successfully logged transaction: {tx.description} (R{tx.amount})")
        return "SUCCESS"
    except Exception as e:
        conn.rollback()
        print(f"❌ Database Insertion Failed: {e}")
        return "ERROR"
    finally:
        cursor.close()
        conn.close()

# =====================================================================
# 3. INTERACTIVE DATA EXECUTION BLOCK (LOCAL UNIT TESTING)
# =====================================================================
if __name__ == "__main__":
    # Mock structured JSON dictionary mimicking a flawless OpenAI transaction parse
    mock_json_from_ai = {
        "category": "Service",
        "description": "Skin fade haircut",
        "amount": 250.00,
        "payment_method": "Card"  # Fixed missing parameter constraint
    }
    
    print("🔄 Running Pydantic validation on mock transaction payload...")
    
    try:
        # Validate data shapes matching target field definitions
        validated_tx = FinancialTransaction(**mock_json_from_ai)
        print("🛡️ Data validation passed! Attempting Render cloud insertion...")
        
        # Deploy structural row entry directly to the active cloud container
        log_transaction_to_db(validated_tx)
        
    except Exception as e:
        print(f"❌ Structural Validation Error: {e}")
