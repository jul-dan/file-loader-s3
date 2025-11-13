# Utilisation d'une image Python slim pour réduire la taille
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="your-email@example.com"
LABEL description="Flask S3 File Uploader with OIDC support"

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Création d'un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Répertoire de travail
WORKDIR /app

# Copie des dépendances en premier (pour optimiser le cache Docker)
COPY requirements.txt .

# Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code de l'application
COPY app.py .

# Changement de propriétaire des fichiers
RUN chown -R appuser:appuser /app

# Création du répertoire pour le token OIDC (sera monté en volume)
RUN mkdir -p /var/run/secrets/eks.amazonaws.com/serviceaccount && \
    chown -R appuser:appuser /var/run/secrets

# Passage à l'utilisateur non-root
USER appuser

# Exposition du port 8080
EXPOSE 8080

# Health check pour vérifier que l'application répond
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Commande de démarrage avec gunicorn pour la production
# - bind sur 0.0.0.0:8080
# - 4 workers (ajustable selon les ressources)
# - timeout de 120s pour les gros fichiers
# - log level info
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
