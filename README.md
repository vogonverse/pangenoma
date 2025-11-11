# PanForest: Análisis de Predictibilidad en Pangenomas Bacterianos

> Basado en la metodología de [Beavan et al. (2024) *PNAS*](https://doi.org/10.1073/pnas.2304934120): *"Contingency, repeatability, and predictability in the evolution of a prokaryotic pangenome"*

## Workflow 

Este pipeline implementa un flujo de trabajo para identificar **patrones deterministas** en la evolución del pangenoma bacteriano. Utilizando aprendizaje automático (Random Forests) y métodos comparativos filogenéticos (estadístico D de Fritz-Purvis), determina si los patrones de presencia/ausencia de genes son **predecibles** o si ocurren de manera aleatoria a través de la evolucion de los genomas bacterianos.