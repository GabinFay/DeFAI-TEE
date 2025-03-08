from dfllama import DefiLlamaClient
import json

# Initialize the DeFiLlama client
client = DefiLlamaClient()

# Retrieve details about the SparkDEX protocol
#protocol_slug = 'sparkdex-v3.1' #sparkdex-v3 sparkdex-perps
protocol_slug = 'sparkdex-perps'
protocol_info = client.get_protocol(protocol_slug)

# Save the retrieved information to a text file
output_file = f"{protocol_slug}_info.txt"
with open(output_file, 'w') as f:
    # Convert the protocol info to a formatted string
    if isinstance(protocol_info, dict):
        # Pretty print the JSON with indentation for readability
        f.write(json.dumps(protocol_info, indent=4))
    else:
        # If it's not a dict, convert to string
        f.write(str(protocol_info))

print(f"Protocol information saved to {output_file}")
