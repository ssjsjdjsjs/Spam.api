from flask import Flask, request, jsonify
import requests
import json
import threading
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

def load_tokens():
    regions = ["ind", "br", "sg", "eu", "ru", "id", "tw", "us", "vn", "th", "me", "pk", "cis", "bd", "sac"]
    all_tokens = []
    
    for region in regions:
        file_name = f"token_{region}.json"
        try:
            with open(file_name, "r") as file:
                data = json.load(file)
            # Append a tuple (region, token) for each token in the file
            tokens = [(region, item["token"]) for item in data]
            all_tokens.extend(tokens)
        except Exception as e:
            print(f"Error loading tokens from {file_name}: {e}")
    
    return all_tokens

def send_friend_request(uid, region, token, results):
    # Encrypt the uid and generate the payload
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)
    
    # Build the URL dynamically based on the region
    url = f"https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB48"
    }

    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            results["success"] += 1
        else:
            results["failed"] += 1
    except Exception as e:
        print(f"Error sending request for region {region} with token {token}: {e}")
        results["failed"] += 1

@app.route("/send_requests", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")

    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400

    tokens_with_region = load_tokens()
    if not tokens_with_region:
        return jsonify({"error": "No tokens found in any token file"}), 500

    results = {"success": 0, "failed": 0}
    threads = []

    # Iterate over tokens from all regions (limit to first 110 requests if desired)
    for region, token in tokens_with_region[:100]:
        thread = threading.Thread(target=send_friend_request, args=(uid, region, token, results))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    status = 1 if results["success"] != 0 else 2  # If at least one success, status is 1; otherwise 2

    return jsonify({
        "success_count": results["success"],
        "failed_count": results["failed"],
        "status": status
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)