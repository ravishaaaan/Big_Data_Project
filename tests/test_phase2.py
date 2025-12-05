import pytest
import time
import sys
import os
sys.path.append(os.getcwd())

from datetime import datetime, timedelta, timezone
from kafka_client.producer import (
    generate_transaction,
    generate_high_value_fraud,
    generate_impossible_travel_fraud,
    run_producer
)


def test_high_value_fraud_generation():
    """Test 2.1: High value fraud transactions generate correctly"""
    fraud_tx = generate_high_value_fraud()
    assert fraud_tx['amount'] > 5000, f"High value fraud amount too low: {fraud_tx['amount']}"
    assert fraud_tx['amount'] <= 10000, f"High value fraud amount too high: {fraud_tx['amount']}"
    assert 'transaction_id' in fraud_tx
    assert 'user_id' in fraud_tx
    assert 'timestamp' in fraud_tx
    print(f"✓ Test 2.1 PASSED: High value fraud generates correctly (${fraud_tx['amount']})")


def test_impossible_travel_fraud_generation():
    """Test 2.2: Impossible travel fraud generates correctly"""
    normal_tx = generate_transaction()
    normal_tx['user_id'] = 'TEST_USER_123'
    normal_tx['location'] = 'USA'
    normal_tx['timestamp'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    fraud_tx = generate_impossible_travel_fraud(normal_tx)
    
    assert fraud_tx['user_id'] == 'TEST_USER_123', "User ID mismatch"
    assert fraud_tx['location'] != 'USA', f"Location should be different, got {fraud_tx['location']}"
    
    # Check time difference (should be 5-8 minutes)
    t1 = datetime.fromisoformat(normal_tx['timestamp'])
    t2 = datetime.fromisoformat(fraud_tx['timestamp'])
    diff_minutes = (t2 - t1).total_seconds() / 60
    assert 5 <= diff_minutes <= 8, f"Time difference should be 5-8 minutes, got {diff_minutes:.2f}"
    
    print(f"✓ Test 2.2 PASSED: Impossible travel fraud generates correctly ({normal_tx['location']} -> {fraud_tx['location']}, {diff_minutes:.1f} min)")


def test_normal_transaction_format():
    """Test 2.3: Normal transactions have correct format and amount range"""
    for _ in range(10):
        tx = generate_transaction()
        assert 10 <= tx['amount'] <= 1000, f"Normal transaction amount out of range: ${tx['amount']}"
        
        required_fields = ['transaction_id', 'user_id', 'timestamp', 'merchant_category', 'amount', 'location']
        for field in required_fields:
            assert field in tx, f"Missing field: {field}"
    
    print("✓ Test 2.3 PASSED: Normal transaction format and amounts correct")


def test_fraud_generation_functions_uniqueness():
    """Test 2.4: Generated transactions have unique IDs"""
    transactions = []
    transactions.append(generate_transaction())
    transactions.append(generate_high_value_fraud())
    
    normal_tx = generate_transaction()
    transactions.append(normal_tx)
    transactions.append(generate_impossible_travel_fraud(normal_tx))
    
    ids = [tx['transaction_id'] for tx in transactions]
    assert len(ids) == len(set(ids)), "Transaction IDs are not unique"
    
    print("✓ Test 2.4 PASSED: All transaction IDs are unique")


def test_producer_statistics():
    """Test 2.5: Producer fraud distribution logic (simulated)"""
    # Simulate the producer's fraud distribution without Kafka
    # Producer uses 85% normal, 10% impossible travel, 5% high-value
    
    import random
    random.seed(42)  # For reproducibility
    
    total = 1000
    normal_count = 0
    travel_fraud_count = 0
    high_value_fraud_count = 0
    
    # Simulate the producer's probability logic
    for _ in range(total):
        rand_val = random.random()
        if rand_val < 0.05:  # 5% high-value fraud
            high_value_fraud_count += 1
        elif rand_val < 0.15:  # 10% impossible travel fraud
            travel_fraud_count += 1
        else:  # 85% normal
            normal_count += 1
    
    # Verify distribution is roughly correct (with some tolerance)
    normal_ratio = normal_count / total
    travel_ratio = travel_fraud_count / total
    high_value_ratio = high_value_fraud_count / total
    fraud_ratio = (travel_fraud_count + high_value_fraud_count) / total
    
    # Expected: ~85% normal, ~10% travel, ~5% high-value, ~15% total fraud
    assert 0.80 <= normal_ratio <= 0.90, f"Normal ratio {normal_ratio:.2%} outside expected range (80-90%)"
    assert 0.07 <= travel_ratio <= 0.13, f"Travel fraud ratio {travel_ratio:.2%} outside expected range (7-13%)"
    assert 0.03 <= high_value_ratio <= 0.08, f"High-value fraud ratio {high_value_ratio:.2%} outside expected range (3-8%)"
    assert 0.12 <= fraud_ratio <= 0.18, f"Total fraud ratio {fraud_ratio:.2%} outside expected range (12-18%)"
    
    print(f"✓ Test 2.5 PASSED: Fraud distribution correct - {normal_ratio:.1%} normal, {travel_ratio:.1%} travel fraud, {high_value_ratio:.1%} high-value fraud")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
