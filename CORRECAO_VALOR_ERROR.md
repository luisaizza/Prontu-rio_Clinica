# 🔧 Correção de Erro - ValueError

## ❌ Erro Encontrado

```
ValueError: invalid literal for int() with base 10: 'PROF_ID'
```

### Causa
Na linha 180 de `agendar_servico.html`, o código tentava usar um placeholder `'PROF_ID'` com `url_for()`:

```html
fetch(`{{ url_for('horarios_disponiveis', profissional_id='PROF_ID') }}`.replace('PROF_ID', profissional_id) + `?data=${data}`)
```

O Flask valida os parâmetros de rota no momento da geração da URL, então não aceita strings como `'PROF_ID'` onde espera um inteiro (`<int:profissional_id>`).

---

## ✅ Solução Aplicada

Construir a URL dinamicamente em JavaScript, sem usar `url_for()`:

```html
fetch(`/agenda/horarios-disponiveis/${profissional_id}?data=${data}`)
```

**Mudança:**
- `agendar_servico.html` linha 180

**Resultado:**
- ✅ Sem erro de validação
- ✅ URL construída dinamicamente
- ✅ AJAX funciona corretamente

---

## 🧪 Teste

1. Faça login como `luisaizza / 123`
2. Vá para Home
3. Clique "Novo Agendamento"
4. Selecione um paciente
5. Complete o formulário:
   - Profissional: SARAH
   - Serviço: (qualquer um)
   - Data: data futura
6. Veja os horários carregarem ✅

---

## 📝 Status

**Status:** ✅ CORRIGIDO  
**Data:** 10 de Novembro de 2025  
**Arquivo:** `agendar_servico.html`  
**Linhas modificadas:** 1 (linha 180)
