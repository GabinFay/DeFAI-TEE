# Polygon Bot

A confidential bot designed to interact with blockchain environments and potentially other services, running within a secure enclave.

## Features

*   Secure execution within a Trusted Execution Environment (TEE).
*   Interaction with Ethereum, Base, and Flare networks.
*   Configurable via environment variables.
*   Containerized deployment using Docker.

## Getting Started

### Prerequisites

*   Python 3.x
*   pip (Python package installer)
*   Docker (optional, for containerized deployment)
*   Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url> # Replace with your actual repository URL
    cd flare-bot
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    Copy the template file `.env.template` to a new file named `.env`:
    ```bash
    cp .env.template .env
    ```
    Open the `.env` file and fill in the required values with your specific configuration details (API keys, RPC URLs, wallet information, etc.). **Never commit your `.env` file to version control.**

## Usage

### Running Locally

Ensure your virtual environment is activated and your `.env` file is configured.

```bash
# Example command to run the bot (Update if necessary based on your entry point)
# python src/main.py  # Or potentially a script from the scripts/ directory
echo "Please update this command with the actual way to run the bot."
```
*Note: Check the `src/` or `scripts/` directory for the main execution script or command.*

### Running with Docker

1.  **Build the Docker image:**
    Make sure Docker is running.
    ```bash
    docker build -t flare-bot .
    ```

2.  **Run the Docker container:**
    Ensure your `.env` file is correctly configured in the project root directory.
    ```bash
    docker run --env-file .env flare-bot
    ```
    *(Note: For TEE deployment, refer to the specific instructions related to confidential VMs and the `TEE_IMAGE_REFERENCE` variable).*

## Configuration

The bot uses environment variables for configuration, loaded from the `.env` file at runtime. The following variables are defined in `.env.template`:

*   `INSTANCE_NAME`: Name for the confidential VM instance (e.g., `flare-swap-app`).
*   `TEE_IMAGE_REFERENCE`: Docker image reference for the TEE (e.g., `ghcr.io/your-username/your-repo/flare-swap-app:latest`).
*   `SIMULATE_ATTESTATION`: Set to `true` to simulate attestation if needed (`false` by default).
*   `GITHUB_TOKEN`: Your GitHub personal access token (if required by the bot).
*   `GEMINI_API_KEY`: Your API key for Google Gemini services.
*   `ETHEREUM_RPC_URL`: RPC endpoint URL for the Ethereum network.
*   `BASE_RPC_URL`: RPC endpoint URL for the Base network.
*   `POLYGON_RPC_URL`: RPC endpoint URL for the Flare network.
*   `WALLET_ADDRESS`: Your blockchain wallet address used by the bot.
*   `PRIVATE_KEY`: The private key associated with the `WALLET_ADDRESS`. **Handle with extreme care.**
*   `REACT_APP_RAINBOW_PROJECT_ID`: Project ID for RainbowKit (if used in a related frontend).

## Testing

To run the automated tests (assuming tests are located in the `tests/` directory and use `pytest`):

```bash
pip install pytest # If not already installed
pytest tests/
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[Specify the project license here, e.g., MIT, Apache 2.0, etc.] 
