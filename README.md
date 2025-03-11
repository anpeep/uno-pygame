# Unobot

## Vajalike lisade alla laadimine    
Ava käsurida (<kbd>alt</kbd>+<kbd>F12</kbd> või vali alt vasakult menüüst terminal).  
<img src="images/going_to_terminal.png" width=75% />

Peale seda sisesta konsooli järgnev käsk, vajuta <kbd>Enter</kbd> ning oota kuni see lõpetab.  
```bash
pip install py-cord audioop-lts python-dotenv
```
<img src="images/pip_install.png" width=50% />

## Tokeni lisamine  
Ava või loo `.env` fail ning lisa `TOKEN=` lõppu enda discordi boti token.
<img src="images/adding_bot_token.png" width=75% />

## Boti jooksutamine 🐍
Ava jälle main.py fail. Kõige üleval on selline rida
```python
bot = commands.Bot(command_prefix="!", intents=intents)
```
Muuda seal "!" mingi muu sümboli või emoji vastu (emojisid saab valida vajutades <kbd>Win</kbd>+<kbd>.</kbd>), näiteks
```python
bot = commands.Bot(command_prefix="🍪", intents=intents)
```

Üleval ribal vajuta rohelist kolmnurka ning siis peaks bot tööle minema.
<img src="images/running_bot.png" width=66% />