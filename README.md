# PanForest: Análisis de Predictibilidad en Pangenomas Bacterianos

> Basado en la metodología de [Beavan et al. (2024) *PNAS*](https://doi.org/10.1073/pnas.2304934120): *"Contingency, repeatability, and predictability in the evolution of a prokaryotic pangenome"*

## Descripción

Este pipeline implementa un flujo de trabajo para identificar **patrones deterministas** en la evolución del pangenoma bacteriano. Utilizando aprendizaje automático (Random Forest) y métodos comparativos filogenéticos (estadístico D de Fritz-Purvis), determina si los patrones de presencia/ausencia de genes son **predecibles** o si ocurren de manera aleatoria a través de la evolución de los genomas bacterianos.

---

Pasos a seguir para ejecutar el pipeline (v1.0):

### 1. Instalar Miniconda

**Linux:**
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### 2. Clonar el repositorio
```bash
git clone https://github.com/vogonverse/pangenoma.git
cd pangenoma
```

### 3. Crear entorno conda con YAML del repositorio
```bash
conda env create -f environment.yaml
conda activate pangenoma
```

### 4. Cambiar a versión estable
```bash
git fetch --tags
git checkout v1.0
```

---

## Ejecución

**Dry run** (verificar pipeline sin ejecutar):
```bash
snakemake -n
```

**Ejecutar el pipeline completo:**
```bash
snakemake --cores 40 results/database/network.db --use-conda --conda-frontend conda
```

Ajustar --cores según núcleos disponibles