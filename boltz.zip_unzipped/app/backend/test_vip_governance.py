#!/usr/bin/env python3
"""
Focused test for VIP governance features
Tests proposal creation, voting, and execution flow
"""

import requests
import json

BASE_URL = "https://carbon-rider-rewards.preview.emergentagent.com/api"
ADMIN_TOKEN = "poc_token_poc_admin"
USER_A_TOKEN = "poc_token_poc_user_a"
USER_B_TOKEN = "poc_token_poc_user_b"

def api_call(method, endpoint, token=None, data=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            r = requests.post(url, json=data, headers=headers, timeout=10)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

print("\n" + "="*80)
print("VIP GOVERNANCE FLOW TEST")
print("="*80)

# Step 1: Check if user_b can be upgraded to VIP
print("\n1. Checking user_b subscription status...")
status, data = api_call("GET", "subscriptions/me", token=USER_B_TOKEN)
print(f"   User B tier: {data.get('tier')}")
print(f"   Voting power: {data.get('voting_power', {}).get('total')}")

if data.get('tier') != 'vip':
    print("\n2. Attempting to upgrade user_b to VIP...")
    status, sub_data = api_call("POST", "subscriptions/subscribe", token=USER_B_TOKEN,
                               data={"tier": "vip", "payment_method": "rmr"})
    if status == 200:
        print("   ✅ User B upgraded to VIP")
    else:
        print(f"   ⚠️  Cannot upgrade: {sub_data.get('detail', 'Unknown error')}")
        print("   Note: User needs 2000 RMR balance")

# Step 2: Try to create a proposal as VIP
print("\n3. Creating proposal as VIP user...")
status, prop_data = api_call("POST", "governance/proposals", token=USER_B_TOKEN,
                            data={
                                "type": "vehicle_add",
                                "title": "Add Segway Vehicle Type",
                                "description": "Segways are eco-friendly personal transporters that should be included in our vehicle options.",
                                "duration_days": 7,
                                "metadata": {
                                    "vehicle_id": "segway",
                                    "label": "Segway",
                                    "g_per_km": 6
                                }
                            })

if status == 200:
    proposal_id = prop_data.get('proposal_id')
    print(f"   ✅ Proposal created: {proposal_id}")
    print(f"   Status: {prop_data.get('status')}")
    print(f"   Type: {prop_data.get('type')}")
    
    # Step 3: Vote on the proposal
    print("\n4. Voting on proposal as Pro user (user_a)...")
    status, vote_data = api_call("POST", f"governance/proposals/{proposal_id}/vote",
                                token=USER_A_TOKEN,
                                data={"choice": "yes"})
    if status == 200:
        print(f"   ✅ Vote cast successfully")
        print(f"   Voting power used: {vote_data.get('vote', {}).get('voting_power')}")
    else:
        print(f"   ❌ Vote failed: {vote_data.get('detail')}")
    
    # Step 4: Try to vote again (should fail)
    print("\n5. Attempting to re-vote (should fail)...")
    status, vote_data2 = api_call("POST", f"governance/proposals/{proposal_id}/vote",
                                 token=USER_A_TOKEN,
                                 data={"choice": "no"})
    if status == 400 and 'already voted' in str(vote_data2.get('detail', '')).lower():
        print(f"   ✅ Re-voting blocked correctly")
    else:
        print(f"   ❌ Unexpected result: {status} - {vote_data2.get('detail')}")
    
    # Step 5: Get proposal details
    print("\n6. Getting proposal details...")
    status, prop_detail = api_call("GET", f"governance/proposals/{proposal_id}", token=USER_A_TOKEN)
    if status == 200:
        print(f"   ✅ Proposal retrieved")
        print(f"   Vote counts: {prop_detail.get('vote_counts')}")
        print(f"   Voting power: {prop_detail.get('voting_power')}")
        print(f"   My vote: {prop_detail.get('my_vote', {}).get('choice')}")
    
    # Step 6: Admin finalize
    print("\n7. Admin finalizing proposal...")
    status, final_data = api_call("POST", f"admin/governance/proposals/{proposal_id}/finalize",
                                 token=ADMIN_TOKEN)
    if status == 200:
        final_status = final_data.get('proposal', {}).get('status')
        print(f"   ✅ Proposal finalized")
        print(f"   Final status: {final_status}")
        
        # Step 7: If passed, execute it
        if final_status == 'passed':
            print("\n8. Admin executing passed proposal...")
            status, exec_data = api_call("POST", f"admin/governance/proposals/{proposal_id}/execute",
                                       token=ADMIN_TOKEN)
            if status == 200:
                print(f"   ✅ Proposal executed")
                result = exec_data.get('proposal', {}).get('execution_result', {})
                print(f"   Execution result: {result}")
                
                # Step 8: Verify vehicle was added
                print("\n9. Verifying vehicle was added to protocol...")
                # Try to start a ride with the new vehicle
                status, ride_data = api_call("POST", "rides/start", token=USER_A_TOKEN,
                                           data={"vehicle_type": "segway"})
                if status == 200:
                    print(f"   ✅ New vehicle 'segway' is usable in rides")
                    # Clean up - finish the ride
                    ride_id = ride_data.get('ride_id')
                    api_call("POST", f"rides/{ride_id}/finish", token=USER_A_TOKEN,
                           data={"total_distance": 1.0, "gps_trace": []})
                else:
                    print(f"   ⚠️  Vehicle not immediately usable: {ride_data.get('detail')}")
            else:
                print(f"   ❌ Execute failed: {exec_data.get('detail')}")
        else:
            print(f"   ⚠️  Proposal not passed (status: {final_status})")
    else:
        print(f"   ❌ Finalize failed: {final_data.get('detail')}")
    
elif status == 403:
    print(f"   ❌ User not VIP: {prop_data.get('detail')}")
else:
    print(f"   ❌ Proposal creation failed: {status} - {prop_data.get('detail')}")

print("\n" + "="*80)
print("VIP GOVERNANCE FLOW TEST COMPLETE")
print("="*80 + "\n")
