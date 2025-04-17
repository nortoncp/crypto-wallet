from apscheduler.schedulers.background import BackgroundScheduler
from app.services.analise_tecnica import gerar_sinais_entrada

def iniciar_agendador():
    scheduler = BackgroundScheduler()
    scheduler.add_job(gerar_sinais_entrada, 'interval', seconds=30)
    scheduler.start()

# Verificar os jobs agendados
    print("[AGENDADOR] Jobs ativos:")
    for job in scheduler.get_jobs():
        print(f"  - {job}")

