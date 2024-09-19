# PlotBot

#Backend
- Built using Python-3.8 V2 .
## Prerequisite
- Install Function tools. [https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=windows%2Cbash%2Cazure-cli%2Cbrowser](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=windows%2Cbash%2Cazure-cli%2Cbrowser)

## Steps to run local

```sh
cd backend 

.venv\Scripts\Activate.ps1  

pip install -r requirements.txt

func --version 

func start --verbose  
```

## Deploy to Azure
```sh
func azure functionapp publish plotbotfa
```