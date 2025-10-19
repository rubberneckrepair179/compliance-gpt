#!/bin/bash
# Quick activation helper for compliance-gpt POC environment

# Activate virtual environment
source venv/bin/activate

# Display status
echo "✓ compliance-gpt POC environment activated"
echo ""
echo "Quick commands:"
echo "  python scripts/cli.py test-setup    # Verify dependencies"
echo "  python scripts/cli.py --help        # Show all commands"
echo ""
echo "Next steps:"
echo "  1. Copy test documents to test_data/raw/"
echo "  2. Configure .env with API keys"
echo "  3. Run document inspection"
