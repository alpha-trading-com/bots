INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .balance-container {{
            background-color: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .balance-title {{
            font-size: 18px;
            color: #333;
            margin-bottom: 10px;
        }}
        .balance-amount {{
            font-size: 24px;
            color: #2c5282;
            font-weight: bold;
        }}
        .stake-form {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stake-form input, .stake-form select {{
            width: 100%;
            padding: 8px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .stake-form button {{
            background-color: #2c5282;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            position: relative;
            min-width: 100px;
        }}
        .stake-form button:hover {{
            background-color: #2a4365;
        }}
        .stake-form button:disabled {{
            background-color: #718096;
            cursor: not-allowed;
        }}
        .stake-form button.loading {{
            color: transparent;
        }}
        .stake-form button.loading::after {{
            content: "";
            position: absolute;
            width: 16px;
            height: 16px;
            top: 50%;
            left: 50%;
            margin: -8px 0 0 -8px;
            border: 2px solid #ffffff;
            border-radius: 50%;
            border-right-color: transparent;
            animation: button-loading-spinner 0.75s linear infinite;
        }}
        @keyframes button-loading-spinner {{
            from {{
                transform: rotate(0deg);
            }}
            to {{
                transform: rotate(360deg);
            }}
        }}
    </style>
</head>
<body>
    <h1>Dashboard</h1>
    {balance_html}
    
    <div class="stake-form">
        <h2>Stake TAO</h2>
        <form id="stakeForm">
            <div>
                <label for="tao_amount">Amount (TAO):</label>
                <input type="number" id="tao_amount" name="tao_amount" step="0.1" required>
            </div>
            <div>
                <label for="netuid">NetUID:</label>
                <input type="number" id="netuid" name="netuid" required>
            </div>
            <div>
                <label for="wallet_name">Wallet:</label>
                <select id="wallet_name" name="wallet_name">
                    <option value="stake_2">stake_2</option>
                    <option value="sangar_ck2">sangar_ck2</option>
                </select>
            </div>
            <div>
                <label for="dest_hotkey">Destination Hotkey:</label>
                <input type="text" id="dest_hotkey" name="dest_hotkey" value="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v" required>
            </div>
            <div>
                <label for="rate_tolerance">Rate Tolerance:</label>
                <input type="number" id="rate_tolerance" name="rate_tolerance" step="0.0001" value="0.005" required>
            </div>
            <button type="submit">Stake</button>
        </form>
    </div>
    <div class="stake-form">
        <h2>Unstake TAO</h2>
        <form id="unstakeForm">
            <div>
                <label for="unstake_netuid">NetUID:</label>
                <input type="number" id="unstake_netuid" name="netuid" required>
            </div>
            <div>
                <label for="unstake_wallet_name">Wallet:</label>
                <select id="unstake_wallet_name" name="wallet_name">
                    <option value="stake_2">stake_2</option>
                    <option value="sangar_ck2">sangar_ck2</option>
                </select>
            </div>
            <div>
                <label for="unstake_dest_hotkey">Destination Hotkey:</label>
                <input type="text" id="unstake_dest_hotkey" name="dest_hotkey" value="5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v" required>
            </div>
            <button type="submit">Unstake</button>
        </form>
    </div>

    <script>
        document.getElementById('unstakeForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const submitButton = e.target.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            
            const formData = new FormData(e.target);
            const params = new URLSearchParams(formData);
            
            try {{
                const response = await fetch(`/unstake?${{params.toString()}}`);
                const result = await response.json();
                alert(result.message);
            }} catch (error) {{
                alert('Error: ' + error.message);
            }} finally {{
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
            }}
        }});
    </script>
    <script>
        document.getElementById('stakeForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const submitButton = e.target.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            
            const formData = new FormData(e.target);
            const params = new URLSearchParams(formData);
            
            try {{
                const response = await fetch(`/stake?${{params.toString()}}`);
                const result = await response.json();
                alert(result.message);
            }} catch (error) {{
                alert('Error: ' + error.message);
            }} finally {{
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
            }}
        }});
    </script>
</body>
</html>

"""
