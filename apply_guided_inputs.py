from __future__ import annotations

"""Melhora as instruções dos formulários sem alterar a camada científica/dados.

Execute na raiz do repositório (ao lado de anthocyanin_ui.py):
    python apply_guided_inputs.py

Cria backup datado antes de escrever. Não altera CSVs, referências ou modelos científicos.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

MARKER = "# GUI_GUIDANCE_PATCH_V1"

NEW_ROW_STAB = r'''def _row_stab() -> dict:
    """Campos do método diferencial de pH, com orientação no próprio formulário."""
    return {
        "batch_id": st.text_input("Lote independente (batch_id)", placeholder="ex.: B01", help="Identifique uma extração independente de repolho roxo. Use o mesmo código em todas as medições derivadas dessa extração; extrações feitas em dias/preparos distintos recebem códigos distintos."),
        "formulation": st.text_input("Formulação (formulation)", placeholder="ex.: F_NATIVE ou F_PH3", help="Descreva a formulação de modo padronizado. Ex.: F_NATIVE = extrato no pH natural; F_PH3 = alíquota ajustada para pH 3,0. Use o protocolo real adotado e não altere o significado do código durante o estudo."),
        "storage_condition": st.text_input("Condição de armazenamento", placeholder="ex.: BASELINE, C4_DARK, C25_DARK", help="Use BASELINE para a medição basal do dia 0 feita antes da distribuição; C4_DARK para 4 °C no escuro; C25_DARK para 25 °C no escuro. Registre desvios no campo de observações."),
        "day": st.text_input("Tempo de armazenamento (dias)", placeholder="ex.: 0, 3, 7, 10, 14 ou 28", help="Número de dias desde o início do armazenamento. Dia 0 é a referência basal da mesma combinação lote + formulação."),
        "vial_id": st.text_input("Código do frasco/amostra (vial_id)", placeholder="ex.: B01_PH3_D07_C4_R1", help="Código único da unidade física analisada. O protocolo recomenda abrir cada frasco uma única vez; não conte leituras repetidas do mesmo frasco como lotes independentes."),
        "replicate": st.text_input("Número da réplica técnica", placeholder="ex.: 1", help="Número inteiro positivo que identifica uma réplica dentro do mesmo lote/condição/tempo. Réplicas técnicas ajudam a estimar variação de medição, mas não substituem extrações independentes."),
        "pH_storage": st.text_input("pH do extrato no armazenamento", placeholder="ex.: 3.02", help="pH realmente medido no extrato no momento da coleta/análise, obtido com pHmetro calibrado. Não substitua pela meta de pH sem medir."),
        "a520_ph1": st.text_input("Absorbância a 520 nm — tampão pH 1,0", help="Leitura UV-Vis da alíquota diluída em tampão pH 1,0, a 520 nm. Valor adimensional do equipamento; use o branco/SOP do laboratório."),
        "a700_ph1": st.text_input("Absorbância a 700 nm — tampão pH 1,0", help="Leitura UV-Vis da mesma preparação em tampão pH 1,0, a 700 nm, usada como correção de turbidez no método diferencial de pH."),
        "a520_ph45": st.text_input("Absorbância a 520 nm — tampão pH 4,5", help="Leitura UV-Vis da alíquota preparada em tampão pH 4,5, a 520 nm, seguindo o mesmo SOP adotado para todas as amostras."),
        "a700_ph45": st.text_input("Absorbância a 700 nm — tampão pH 4,5", help="Leitura UV-Vis da mesma preparação em tampão pH 4,5, a 700 nm, usada como correção de turbidez."),
        "dilution_factor": st.text_input("Fator de diluição (DF)", placeholder="ex.: 10", help="Fator total aplicado antes da leitura, definido pelo protocolo de preparo. Ex.: uma diluição 1:10 corresponde a DF=10 se essa for a convenção do SOP. Não estime: calcule a partir dos volumes utilizados."),
        "path_length_cm": st.text_input("Caminho óptico da cubeta (cm)", placeholder="ex.: 1.0", help="Comprimento do caminho óptico em centímetros, conforme a cubeta e o equipamento. Use 1,0 somente se a cubeta tiver caminho óptico de 1 cm."),
        "notes": st.text_area("Observações / desvios do protocolo", height=70, placeholder="ex.: precipitado observado; leitura repetida após conferir o branco", help="Registre condições reais relevantes, ocorrências, desvios, identificação do SOP e motivos para repetir/excluir uma leitura. Não coloque aqui valores estimados como se fossem medidos."),
    }'''

NEW_ROW_COLOR = r'''def _row_color() -> dict:
    """Campos de cor; conserva RGB original e só aceita CIELAB quando medido externamente."""
    return {
        "batch_id": st.text_input("Lote independente (batch_id)", placeholder="ex.: B01", help="Use o mesmo ID da extração correspondente na tabela de estabilidade."),
        "formulation": st.text_input("Formulação", placeholder="ex.: F_NATIVE ou F_PH3", help="Código consistente com o cadastro de estabilidade; descreva no protocolo a composição/acidificante de cada código."),
        "storage_condition": st.text_input("Condição de armazenamento", placeholder="ex.: BASELINE, C4_DARK ou C25_DARK", help="Use os mesmos códigos padronizados na tabela de estabilidade. BASELINE representa a medição inicial do dia 0."),
        "day": st.text_input("Tempo de armazenamento (dias)", placeholder="ex.: 0, 14 ou 28", help="Dias desde o início do armazenamento. A cor deve ser comparada com uma referência equivalente do dia 0."),
        "vial_id": st.text_input("Código do frasco/amostra", placeholder="ex.: B01_PH3_D14_C4_R1", help="Identifica a unidade física que foi fotografada/medida. Mantenha a ligação com o registro da amostra correspondente."),
        "replicate": st.text_input("Número da réplica técnica", placeholder="ex.: 1", help="Número inteiro positivo da repetição técnica; não o confunda com o número de lote independente."),
        "target_pH": st.text_input("pH-alvo da solução de desafio", placeholder="ex.: 3.0", help="pH nominal do tampão/solução usada para testar a resposta indicadora. Use vazio quando não se aplicou uma solução de pH conhecido."),
        "measured_pH_final": st.text_input("pH final após misturar com o extrato", placeholder="ex.: 3.14", help="pH medido depois da mistura do extrato indicador com a solução/tampão. É diferente do pH-alvo, pois o extrato pode alterar o pH final."),
        "r": st.text_input("Canal vermelho (R), 0–255", placeholder="ex.: 124", help="Canal vermelho extraído da imagem original, em RGB sRGB de 8 bits. Use iluminação, distância, fundo, recipiente e configurações da câmera padronizados."),
        "g": st.text_input("Canal verde (G), 0–255", placeholder="ex.: 82", help="Canal verde da mesma região de interesse e da mesma imagem que R e B. Não use valores de imagens com filtros ou edição não documentada."),
        "b": st.text_input("Canal azul (B), 0–255", placeholder="ex.: 166", help="Canal azul da mesma região de interesse. A interface deriva HSV de RGB; isso não é equivalente a uma medição CIELAB."),
        "L_star": st.text_input("CIELAB L* (opcional)", placeholder="somente se medido/validado", help="Claridade CIELAB de uma medição instrumental ou método validado. Não é o canal vermelho nem deve ser digitado como estimativa visual."),
        "a_star": st.text_input("CIELAB a* (opcional)", placeholder="somente se medido/validado", help="Coordenada verde–vermelho do espaço CIELAB fornecida por instrumento/método validado."),
        "b_star": st.text_input("CIELAB b* (opcional)", placeholder="somente se medido/validado", help="Coordenada azul–amarelo do espaço CIELAB fornecida por instrumento/método validado. Não é o canal B do RGB."),
        "absorbance_max_nm": st.text_input("Comprimento de onda do pico (nm, opcional)", placeholder="ex.: 530", help="Comprimento de onda em que foi observado o pico de absorbância no espectro UV-Vis. Preencha apenas se realizou a varredura."),
        "absorbance_max": st.text_input("Absorbância no pico (opcional)", placeholder="valor do UV-Vis", help="Absorbância medida no comprimento de onda informado acima; mantenha o branco, diluição e condições do SOP consistentes."),
        "notes": st.text_area("Observações / condições da imagem", height=70, placeholder="ex.: iluminação LED branca, exposição bloqueada", help="Registre iluminação, aparelho, aplicativo/método de extração RGB, recipiente e desvios. Guarde as imagens originais fora do CSV conforme o protocolo de dados."),
    }'''

NEW_SIMULATOR = r'''def render_simulator() -> None:
    st.header("Simulador de estabilidade")
    st.markdown("""
    **Para que serve:** explorar como uma curva hipotética de perda de antocianinas mudaria sob temperaturas e fatores de influência diferentes. O modelo usado é de primeira ordem com correção de temperatura por Arrhenius.

    **O que este simulador não faz:** não extrai parâmetros automaticamente das referências, não calcula um pH real a partir do fator de pH e não determina prazo de validade. Os fatores de pH, luz, oxigênio e embalagem são hipóteses explícitas até serem estimados para este extrato por dados apropriados.
    """)
    st.warning("Todos os resultados desta página são SIMULADOS. Não use valores fictícios para preencher lacunas nem apresente a curva como medição, previsão validada ou prova de estabilidade.")

    if not CONFIG_PATH.exists():
        st.info("Arquivo de configuração não encontrado. Execute `python anthocyanin_lab.py init --dir .` na raiz do projeto.")
        return
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Configuração inválida: {exc}")
        return

    st.subheader("1. Parâmetros de referência do modelo")
    st.caption("Preencha somente quando houver uma fonte ou ajuste experimental compatível. Se ainda não tiver meia-vida e energia de ativação justificáveis, não interprete a saída como estimativa do seu extrato.")
    ref_temp = st.number_input(
        "Temperatura de referência (°C)",
        value=float(cfg.get("reference_temperature_c", 25.0)), format="%.2f",
        help="Temperatura à qual corresponde a meia-vida de referência informada abaixo. As duas entradas precisam descrever a mesma condição e unidade de sistema (matriz/solvente/formulação). Não é necessariamente a temperatura em que pretende guardar o produto.",
    )
    ref_hl = st.number_input(
        "Meia-vida de referência (dias)",
        min_value=0.0,
        value=(float(cfg.get("reference_half_life_days", 0)) if cfg.get("reference_half_life_days") is not None else 0.0), format="%.2f",
        help="Tempo estimado para o modelo de primeira ordem reduzir o valor de referência à metade na temperatura acima. Procure esse parâmetro em artigo com matriz, solvente, pH e condições próximas, ou ajuste-o aos seus dados reais. Registre a fonte/condições no caderno; não copie um número de outra matriz sem justificativa.",
    )
    ea = st.number_input(
        "Energia de ativação aparente (kJ/mol)", min_value=0.0,
        value=(float(cfg.get("activation_energy_kj_mol", 0)) if cfg.get("activation_energy_kj_mol") is not None else 0.0), format="%.2f",
        help="Parâmetro que descreve quanto a taxa de degradação muda com a temperatura no modelo de Arrhenius. Idealmente é estimado com taxas medidas em várias temperaturas ou obtido de estudo compatível. Não é uma energia universal das antocianinas; se não há valor defensável, não invente.",
    )
    init_pct = st.number_input(
        "Retenção inicial normalizada (%)", min_value=0.0,
        value=float(cfg.get("initial_retention_pct", 100.0)), format="%.2f",
        help="Valor do instante inicial da curva. Use 100 para expressar retenção relativa ao dia 0; outro valor só faz sentido se houver razão explícita para normalizar a curva de outra forma. Não representa diretamente concentração em mg/L.",
    )
    days = st.text_input(
        "Dias em que deseja calcular a curva",
        value=",".join(str(d) for d in cfg.get("days", [0, 3, 7, 10, 14, 28])),
        help="Lista de tempos em dias, separada por vírgulas (ex.: 0,3,7,14,28). São pontos da saída matemática, não medições que ocorreram de fato.",
    )

    st.subheader("2. Cenários de armazenamento")
    st.caption("Edite a temperatura de cada cenário. Os quatro fatores seguintes multiplicam a taxa de degradação: 1,0 = sem efeito presumido; acima de 1,0 = degradação mais rápida; abaixo de 1,0 = degradação mais lenta. Esses efeitos precisam de evidência para serem interpretados como reais.")
    scenarios = cfg.get("scenarios", [])
    edited_scenarios = []
    for i, s in enumerate(scenarios):
        with st.container(border=True):
            st.markdown(f"**Cenário {i + 1}**")
            sid = st.text_input(f"Identificador do cenário {i + 1}", value=str(s.get("scenario_id", i)), key=f"sim_sid_{i}", help="Código curto, único e consistente, por exemplo C4_DARK. Serve para identificar a curva na tabela/exportação.")
            label = st.text_input(f"Nome do cenário {i + 1}", value=str(s.get("label", "")), key=f"sim_label_{i}", help="Nome legível com a condição real/hipotética (ex.: 4 °C, escuro). Não substitui a identificação completa no protocolo.")
            temp = st.number_input(f"Temperatura do cenário {i + 1} (°C)", value=float(s.get("temperature_c", 4.0)), format="%.2f", key=f"sim_temp_{i}", help="Temperatura que será usada no fator de Arrhenius para esta curva. Compare apenas com faixas suportadas pela fonte/experimento; extrapolações podem ser pouco confiáveis.")
            c1, c2 = st.columns(2)
            with c1:
                ph_f = st.number_input(f"Fator de pH {i + 1}", min_value=0.0, value=float(s.get("pH_factor", 1.0)), format="%.3f", key=f"sim_ph_{i}", help="Multiplicador hipotético da taxa para representar um efeito do pH. Não é o valor de pH (ex.: 3,0) e não calcula esse efeito a partir do pH. Use 1,0 se ainda não mediu/justificou um efeito.")
                light_f = st.number_input(f"Fator de luz {i + 1}", min_value=0.0, value=float(s.get("light_factor", 1.0)), format="%.3f", key=f"sim_light_{i}", help="Multiplicador hipotético para exposição à luz. 1,0 equivale a não alterar a taxa; valores diferentes exigem resultados/estudo compatível para justificá-los.")
            with c2:
                oxygen_f = st.number_input(f"Fator de oxigênio {i + 1}", min_value=0.0, value=float(s.get("oxygen_factor", 1.0)), format="%.3f", key=f"sim_oxygen_{i}", help="Multiplicador hipotético ligado a disponibilidade de oxigênio/espaço de cabeça. Não mede oxigênio no frasco e não deve variar se o estudo não controla/avalia este fator.")
                pkg_f = st.number_input(f"Fator de embalagem {i + 1}", min_value=0.0, value=float(s.get("packaging_factor", 1.0)), format="%.3f", key=f"sim_pkg_{i}", help="Multiplicador hipotético para efeito da embalagem/barreira. Não é um ranking universal de materiais; só use números diferentes de 1,0 com evidência compatível.")
        edited_scenarios.append({
            "scenario_id": sid, "label": label, "temperature_c": temp,
            "pH_factor": ph_f, "light_factor": light_f, "oxygen_factor": oxygen_f,
            "packaging_factor": pkg_f, "notes": s.get("notes", ""),
        })

    st.info("**Antes de executar:** confirme que a meia-vida e a energia de ativação têm uma fonte identificável e condições compatíveis. As referências são consultadas na página Literatura, mas o simulador não seleciona nem aplica os seus valores automaticamente.")
    if st.button("Executar simulação hipotética", type="primary"):
        if ref_hl <= 0 or ea <= 0:
            st.error("Para executar, meia-vida e energia de ativação precisam ser positivas. Não substitua a falta desses parâmetros por valores aleatórios; localize fontes compatíveis ou aguarde dados experimentais.")
            return
        if not edited_scenarios:
            st.error("Não há cenários definidos no arquivo de configuração.")
            return
        try:
            days_list = [float(d.strip()) for d in days.split(",") if d.strip()]
        except ValueError:
            st.error("Não entendi a lista de dias. Use números separados por vírgula, como 0,3,7,14,28.")
            return
        if not days_list or any(d < 0 for d in days_list):
            st.error("Informe pelo menos um dia não negativo.")
            return

        scenario_cfg = {
            "model": "first_order_arrhenius_scenario",
            "purpose": "Exploração de hipóteses; não é previsão validada nem dado experimental.",
            "reference_temperature_c": float(ref_temp),
            "reference_half_life_days": float(ref_hl),
            "activation_energy_kj_mol": float(ea),
            "initial_retention_pct": float(init_pct),
            "days": days_list,
            "scenarios": edited_scenarios,
        }
        try:
            results = lab.simulate_scenarios(scenario_cfg)
        except (ValueError, KeyError) as exc:
            st.error(f"Simulação recusada: {exc}")
            return

        st.success("Cálculo concluído — isso confirma apenas a execução matemática, não a validade científica dos parâmetros.")
        st.dataframe(results, use_container_width=True, height=360)
        st.caption("Origem: SIMULATION_ONLY. Os resultados permanecem separados dos dados experimentais e não demonstram prazo de validade, segurança ou desempenho real do indicador.")'''

NEW_QUERY = r'''def render_query_management() -> None:
    st.header("Consultar e exportar registros")
    st.markdown("Aqui você **visualiza e exporta** registros já salvos; esta página não cadastra nem corrige medições. Para inserir dados novos, use as páginas de cadastro de estabilidade ou cor. Os filtros e arquivos exportados não modificam os CSVs de origem.")

    tab_s, tab_c = st.tabs(["Estabilidade", "Cor"])
    with tab_s:
        st.subheader("Medições de estabilidade")
        st.caption("Cada linha é uma observação de armazenamento usada no método diferencial de pH. Confira batch_id, formulação, condição, dia e unidade física antes de comparar valores.")
        data = read_stability()
        if data.empty:
            st.info("Nenhuma medição de estabilidade gravada ainda.")
        else:
            filtered = _filtered_selection(data)
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Estabilidade)", csv_bytes, "estabilidade_selecionados.csv", mime="text/csv")

    with tab_c:
        st.subheader("Medições de cor")
        st.caption("RGB deve vir de imagem/medição feita em condições padronizadas. HSV é derivado do RGB; CIELAB/ΔE só são usados quando os campos CIELAB foram obtidos por método válido.")
        data = read_color()
        if data.empty:
            st.info("Nenhuma medição de cor gravada ainda.")
        else:
            filtered = _filtered_selection(data)
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Cor)", csv_bytes, "cor_selecionados.csv", mime="text/csv")

    with st.expander("Microbiologia — módulo opcional, não necessário para a pergunta principal atual"):
        st.write("O estudo principal está focado na estabilidade química das antocianinas e na resposta colorimétrica ao pH. Você não precisa cadastrar testes microbiológicos para executar essa parte. Esta área fica apenas para eventual consulta de registros antigos ou uso futuro, caso o projeto passe a avaliar estabilidade microbiológica, segurança ou prazo de validade para uma aplicação específica.")
        micro = read_micro()
        if micro.empty:
            st.caption("Nenhum registro microbiológico. Não é necessário preencher este arquivo para seguir com o estudo principal.")
        else:
            st.dataframe(micro, use_container_width=True, height=260)
            st.download_button("Exportar registros microbiológicos", micro.to_csv(index=False).encode("utf-8"), "microbiologia_registros.csv", mime="text/csv")

    st.divider()
    st.subheader("Como a gravação é protegida")
    st.write("- Novos registros são validados antes da gravação.")
    st.write("- Registros duplicados são recusados; nada é sobrescrito silenciosamente.")
    st.write("- Um backup timestampado do CSV é criado antes de acrescentar novos registros.")'''

NEW_LITERATURE = r'''def render_literature() -> None:
    st.header("Literatura científica")
    st.markdown("Esta página é para **consultar as fontes e entender que tipo de informação cada estudo fornece**; não é um formulário para digitar resultados. Os campos de citação, DOI/URL e localização da fonte permanecem ligados aos registros existentes. A presença de uma referência no catálogo não significa, por si só, que cada valor publicado já foi conferido no texto original.")
    st.info("**Como navegar:** em *Estudos*, consulte a referência bibliográfica, matriz, solvente e limitações; em *Medições*, veja valores publicados e séries no tempo; em *Evidências*, veja resumos cinéticos ou afirmações qualitativas. Mantenha separados valores diretamente reportados e valores calculados a partir deles.")

    tab_st, tab_me, tab_ev = st.tabs(["Estudos e referências", "Medições publicadas", "Evidências e parâmetros"])
    with tab_st:
        st.subheader("Estudos e referências bibliográficas")
        st.caption("Use DOI/URL para abrir a fonte primária e confira se a matriz, o solvente, o pH, a temperatura e o método combinam com o seu estudo.")
        data = read_literature_studies()
        cols = ["study_id", "citation", "doi", "url", "species", "matrix", "solvent", "analysis_unit", "limitations"]
        if not data.empty:
            st.dataframe(data[cols], use_container_width=True, height=360)
        else:
            st.info("Nenhum estudo de literatura carregado.")

    with tab_me:
        st.subheader("Valores e séries temporais publicados")
        st.caption("Cada linha deve manter estudo, tratamento, tempo/unidade, variável/unidade e localização exata da fonte. Valores ausentes na publicação devem continuar vazios; não complete por suposição.")
        data = read_literature_measurements()
        if not data.empty:
            origin = data["data_origin"].fillna("").astype(str)
            reported = data["reported_or_calculated"].fillna("").astype(str)
            st.caption("PUBLISHED_ARTICLE identifica a origem bibliográfica. reported_or_calculated distingue o que foi transcrito da fonte do que foi calculado posteriormente.")
            pub = data[origin == "PUBLISHED_ARTICLE"]
            if not pub.empty:
                pub_cols = ["study_id", "treatment_id", "time_value", "time_unit", "measurement", "value", "value_unit", "standard_deviation", "replicate_count", "source_location", "package_material", "data_origin", "reported_or_calculated"]
                st.dataframe(pub[pub_cols], use_container_width=True, height=360)
            else:
                st.info("Nenhuma medição publicada (PUBLISHED_ARTICLE) encontrada.")
        else:
            st.info("Nenhuma medição de literatura gravada ainda.")

    with tab_ev:
        st.subheader("Evidências narrativas e parâmetros resumidos")
        st.caption("Use a localização da fonte e as condições descritas para rastrear cada informação. Resumos de meia-vida/constante cinética não são equivalentes a uma série temporal completa.")
        data = read_literature_evidence()
        cols = ["study_id", "evidence_type", "evidence_category", "evidence_text", "origin_source", "source_url", "source_location", "conditions", "temperature_c", "pH", "half_life", "k_value", "notes"]
        if not data.empty:
            st.dataframe(data[cols], use_container_width=True, height=360)
        else:
            st.info("Nenhuma evidência de literatura carregada.")

    st.divider()
    st.warning("Antes de usar um valor como parâmetro científico, verifique o texto integral, local exato da tabela/figura, unidade, condição experimental e se é reportado ou calculado. O status de referência não valida automaticamente os números nem autoriza transferi-los para o extrato deste projeto.")'''


def replace_function(src: str, name: str, replacement: str, next_pattern: str) -> str:
    pat = rf"^def {re.escape(name)}\(.*?(?=^{next_pattern})"
    out, n = re.subn(pat, replacement.rstrip() + "\n\n", src, count=1, flags=re.M | re.S)
    if n != 1:
        raise RuntimeError(f"Não localizei com segurança a função {name}; arquivo não será gravado.")
    return out


def patch_source(source: str) -> str:
    if MARKER in source:
        raise RuntimeError("Este patch de orientações já foi aplicado; nada foi alterado.")
    # Replace field definitions and complete pages, using the next stable function/decorator as boundary.
    source = replace_function(source, "_row_stab", NEW_ROW_STAB, r"def render_stability_form\(")
    source = replace_function(source, "render_stability_form", _add_intro_to_stability(), r"@st\.cache_data")
    source = replace_function(source, "_row_color", NEW_ROW_COLOR, r"def render_color_form\(")
    source = replace_function(source, "render_color_form", _add_intro_to_color(), r"@st\.cache_data")
    source = replace_function(source, "render_query_management", NEW_QUERY, r"def _row_micro\(")
    source = replace_function(source, "render_simulator", NEW_SIMULATOR, r"# Contratos de literatura")
    source = replace_function(source, "render_literature", NEW_LITERATURE, r"@st\.cache_data")

    # Provide explicit purpose and help on the ML configuration, without changing training logic.
    needle = '    st.caption("Módulo exploratório do ``anthocyanin_lab.train_ml_model``. "\n               "Por padrão usa somente ``data_origin=EXPERIMENTAL``; literatura exige mapeamento manual.")'
    repl = needle + '\n    st.info("Esta página não é o lugar para cadastrar os dados de bancada. Primeiro preencha medições reais nas páginas de estabilidade/cor e, quando houver linhas suficientes, registre-as conscientemente em `data/raw/ml_observations.csv`. Simulação não pode ser misturada aos dados experimentais. O modelo é exploratório e não serve para declarar prazo de validade.")'
    if source.count(needle) != 1:
        raise RuntimeError("Não localizei o cabeçalho do ML esperado; arquivo não será gravado.")
    source = source.replace(needle, repl, 1)
    source = source.replace('target = st.selectbox("Variável-alvo", lab.ML_ALLOWED_TARGETS)',
                            'target = st.selectbox("Variável-alvo", lab.ML_ALLOWED_TARGETS, help="Escolha o resultado que o modelo tentaria estimar: retention_pct = retenção relativa de antocianinas; tac_mg_c3g_L = teor em equivalentes de cianidina-3-glicosídeo por litro; delta_e_cie76_vs_day0 = diferença de cor CIELAB em relação ao dia 0. Só escolha um alvo quando esses valores tiverem sido medidos/calculados por método documentado.")', 1)
    source = source.replace('include_literature = st.checkbox("Incluir literatura (mapeamento manual)", value=False)',
                            'include_literature = st.checkbox("Incluir literatura (mapeamento manual)", value=False, help="Deixe desmarcado no fluxo normal. A inclusão requer mapeamento manual e pelo menos cinco estudos distintos; ainda assim, a diferença entre matrizes/métodos limita as conclusões.")', 1)

    # Keep the microbiology module and source data intact, but remove it from the main study flow.
    source, n_page = re.subn(r'^\s*"Cadastro de microbiologia",\n', '', source, count=1, flags=re.M)
    source, n_route = re.subn(r'^\s*elif page == "Cadastro de microbiologia":\n\s*render_micro_form\(\)\n', '', source, count=1, flags=re.M)
    if n_page != 1 or n_route != 1:
        raise RuntimeError("Não consegui retirar microbiologia do menu principal com segurança; arquivo não será gravado.")

    # Inject marker and validate that Python can compile the resulting source.
    source = source.replace('from __future__ import annotations\n', 'from __future__ import annotations\n\n' + MARKER + '\n', 1)
    compile(source, "anthocyanin_ui.py", "exec")
    return source


def _add_intro_to_stability() -> str:
    return r'''def render_stability_form() -> None:
    st.header("Cadastro de estabilidade")
    st.markdown("Registre as leituras reais do **método diferencial de pH** para acompanhar a concentração de antocianinas ao longo do armazenamento. Esta página não executa o ensaio: ela guarda os valores medidos no UV-Vis e os metadados da amostra.")
    st.info("Preencha com dados obtidos no laboratório e conforme o SOP. O dia 0 é a referência para retenção; use o mesmo lote e a mesma formulação. Para BASELINE compartilhado, cadastre o dia 0 com `storage_condition=BASELINE`. Campos ainda não medidos devem ficar vazios, nunca estimados.")
    st.caption("Arquivo de destino: data/raw/stability_measurements.csv. Os campos abaixo exibem dicas ao passar o cursor sobre o ícone de ajuda.")
    last = st.session_state.get("stable_last")
    if last:
        if last["status"] == "success":
            st.success(last["message"])
            st.caption("Arquivo atualizado. Próximo registro:")
            if st.button("Cadastrar outra medição", key="stable_new_btn"):
                st.session_state["stable_last"] = None
                st.session_state["stable_form"] = "stability"
        else:
            st.error(last["message"])
            st.session_state["stable_last"] = None
    with st.form("stab_form", clear_on_submit=True):
        row = _row_stab()
        submitted = st.form_submit_button("Salvar medição", type="primary")
    if not submitted:
        return
    df = pd.DataFrame([row])
    result = persist.append_row_safely(STABILITY_CSV, df, STABILITY_KEY, VAL_FUNCTION["stability"])
    st.session_state["stable_last"] = result
    st.rerun()'''


def _add_intro_to_color() -> str:
    return r'''def render_color_form() -> None:
    st.header("Cadastro da resposta de cor")
    st.markdown("Registre a cor do extrato e, quando aplicável, sua resposta após contato com uma solução de pH conhecido. O objetivo é avaliar se a função de indicador continua útil com o armazenamento.")
    st.info("R, G e B são obrigatórios e devem vir da imagem original em condições controladas (mesma iluminação, aparelho, recipiente e região de interesse). O sistema calcula HSV a partir de RGB. L*, a*, b* são opcionais e só devem ser preenchidos se obtidos por instrumento ou método CIELAB validado; a interface não converte RGB em CIELAB automaticamente.")
    st.caption("Arquivo de destino: data/raw/color_measurements.csv. Não preencha observações instrumentais que não foram medidas.")
    last = st.session_state.get("color_last")
    if last:
        if last["status"] == "success":
            st.success(last["message"])
            st.caption("Arquivo atualizado. Próximo registro:")
            if st.button("Cadastrar outra medição", key="color_new_btn"):
                st.session_state["color_last"] = None
                st.session_state["color_form"] = "color"
        else:
            st.error(last["message"])
            st.session_state["color_last"] = None
    with st.form("color_form", clear_on_submit=True):
        row = _row_color()
        submitted = st.form_submit_button("Salvar medição", type="primary")
    if not submitted:
        return
    df = pd.DataFrame([row])
    result = persist.append_row_safely(COLOR_CSV, df, COLOR_KEY, VAL_FUNCTION["color"])
    st.session_state["color_last"] = result
    st.rerun()'''


def main() -> int:
    root = Path.cwd()
    ui_path = root / "anthocyanin_ui.py"
    if not ui_path.is_file():
        print("ERRO: execute este script na raiz do projeto, onde existe anthocyanin_ui.py.", file=sys.stderr)
        return 2
    original = ui_path.read_text(encoding="utf-8")
    try:
        updated = patch_source(original)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    backup = ui_path.with_name(f"anthocyanin_ui.py.before_guidance_{datetime.now():%Y%m%d_%H%M%S}.bak")
    if backup.exists():
        print("ERRO: o backup já existe; nada foi gravado.", file=sys.stderr)
        return 2
    backup.write_text(original, encoding="utf-8")
    ui_path.write_text(updated, encoding="utf-8", newline="\n")
    print("Orientações da interface aplicadas.")
    print(f"Backup criado: {backup.name}")
    print("Alterado apenas: anthocyanin_ui.py")
    print("CSV, referências, persistência, cálculos científicos, simulações e critérios de ML não foram editados.")
    print("Microbiologia saiu do menu principal; código e registros foram preservados e a consulta ficou opcional.")
    print("Agora execute: python -m streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
