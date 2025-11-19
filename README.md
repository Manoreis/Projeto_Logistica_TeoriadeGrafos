# Projeto_Logistica_TeoriadeGrafos
# Projeto de Otimização Logística com Teoria de Grafos

## Visão Geral do Projeto

Este projeto simula e resolve um desafio clássico de logística: otimizar as rotas de entrega de mercadorias entre um armazém central e seus clientes. Utilizando os princípios da Teoria de Grafos, modelamos a rede de transporte para calcular o caminho de menor custo (tempo de viagem) e analisar a resiliência da rede contra falhas.

O código é construído em Python, priorizando performance, modularidade e código limpo, seguindo uma analogia com a estruturação de um sistema profissional de gestão logística, como o SAP (foco em Otimização e Gestão de Exceções).

## Conceitos de Engenharia de Software Aplicados

1. Modularidade e Abstração (Analogia SAP R/3)

O projeto é estruturado em módulos lógicos, assim como o sistema SAP R/3 (foco em SD/MM - Sales and Distribution/Materials Management):

Módulo do Projeto

Função

Analogia com SAP

Representação

Criação e configuração do grafo (Master Data).

Configuração Inicial e Dados Mestre.

Otimização

Cálculo do Caminho Mínimo (Rota Mais Curta).

Otimização de Transporte.

Robustez

Simulação de Falhas e Cálculo de Rotas Alternativas.

Gestão de Exceções e Contingência.

2. Análise de Desempenho

A utilização da biblioteca NetworkX para manipulação de grafos garante que os cálculos (como o algoritmo de Dijkstra) sejam realizados de forma performática e eficiente, ideal para redes logísticas de grande escala.

## Ferramentas e Tecnologias

Linguagem: Python

Manipulação de Grafos: NetworkX (Biblioteca especializada em estruturas de rede)

Visualização de Dados: Matplotlib (Geração de esquemas claros do grafo e rotas)

Técnica: Teoria de Grafos Direcionados e Ponderados (Caminho Mínimo)

## Metodologia e Modelagem

O problema logístico foi traduzido para o universo dos grafos da seguinte forma:

Vértices (Nós): Representam as 5 cidades da nossa sub-rede de transporte (Alpha, Beta, Gamma, Delta, Epsilon).

Arestas Ponderadas (Arcos): Representam as estradas, com o peso definido pelo custo de viagem (Tempo em Minutos).

Grafo Direcionado (DiGraph): Utilizado para refletir que o custo de ida ($A \to B$) pode ser diferente do custo de volta ($B \to A$).

## Cenário de Análise (Alpha até Epsilon)

Análise

Rota

Custo (Tempo)

Caminho Mínimo Ideal

Alpha → Beta → Delta → Epsilon

60 minutos

Caminho Alternativo (Pós-Falha)

Alpha → Beta → Gamma → Epsilon

85 minutos

##Resultados Chave

1. Otimização de Rota

O cálculo do caminho mínimo identificou a rota ideal de 60 minutos. O código utiliza o algoritmo de Dijkstra (via NetworkX) para garantir a precisão da otimização.

2. Análise de Robustez

Simulamos a falha de uma aresta crítica (Beta $\to$ Delta). A rede demonstrou ser robusta:

Impacto: O custo da entrega aumentou em 25 minutos (de 60 para 85 minutos).

Conclusão: A conectividade da rede garante a continuidade da entrega, provando a resiliência do projeto logístico.

# Como Rodar o Projeto (Google Colab / Ambiente Local)

Para executar o código e replicar a análise, siga as instruções abaixo:

Pré-requisitos

Você precisa ter o Python instalado (versão 3.x).

1. Instalação das Bibliotecas

Se estiver rodando em um ambiente local ou Google Colab, execute a seguinte célula para instalar as dependências:

pip install networkx matplotlib


2. Execução do Código

O código Python  com execução no Google Colab contém todas as etapas: construção do grafo, visualização, cálculo de caminho mínimo e análise de robustez.



