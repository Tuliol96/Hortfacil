# HortFácil — Sistema de Gestão para Distribuidora

Aplicação desktop (PySide6) para gestão de uma distribuidora de hortifrúti:
produtos, clientes, pedidos, fechamentos e relatórios.

## Requisitos

- Python 3.11+

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Executar

```bash
python main.py
```

O banco de dados SQLite (`banco/hortfacil.db`) é criado automaticamente na
primeira execução, em `banco/`.

## Estrutura do projeto

```
banco/          conexão e schema do SQLite
models/         dataclasses de domínio (Produto, Cliente, Pedido)
repositories/   acesso a dados (SQL) por entidade
controllers/    regras de aplicação entre UI e repositories
telas/ui/       telas Qt (janela principal + páginas do menu)
```

## Status

Em desenvolvimento. O módulo de **Produtos** está funcional
(model/repository/controller). Clientes, Pedidos, Fechamentos e Relatórios
ainda estão em construção.
