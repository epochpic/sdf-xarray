---
file_format: mystnb
kernelspec:
  name: python3
---

# {{ title }}

- **input deck:** {{ [`UCSD_workshop/{{deck}}/input.deck`](path:https://raw.githubusercontent.com/Status-Mirror/UCSD_workshop/main/{}/input.deck).format(deck) }}
- **Python File:** <path:{{filename}}.py>

```{code-cell} ipython3
:load: ./{{filename}}.py
```