# Agente trader de paper trading

Un agente de IA (Claude Haiku 5.5) opera solo una cuenta de práctica de Alpaca. Despierta cada
30 minutos de 4:00 a 20:00 (hora de Nueva York), de lunes a viernes, mira el mercado y decide:
qué investigar, qué comprar o vender, cuánto, a qué precio y qué protección dejar. Corre en
GitHub Actions; tu laptop puede estar apagada.

No tiene conciencia. Lo que replica es el **proceso** de un trader: observar, investigar,
decidir, apuntar su plan, revisar al cierre qué funcionó y recordarlo al día siguiente.

## Un día del agente

```
4:08   primer despertar: OpenBB baja precios diarios y el calendario de resultados,
       Qlib calcula el momentum 12-1. Sin LLM.
4:08 … 19:38, cada 30 min, el agente despierta y recibe:
       hora y sesión · cuenta y P&L del día · posiciones, stops y órdenes abiertas
       SPY/QQQ hoy · su lista de vigilancia (cartera + top 15 de Qlib + resultados)
       las que más se mueven de su universo · la pantalla de todo el mercado (abajo)
       sus lecciones · lo que hizo hoy y días anteriores
       … y usa sus herramientas hasta 14 veces:
         get_news · get_chart · research (TradingAgents completo) · place_order
         set_stop · cancel_order · note · update_lessons (solo al cierre)
19:38  último despertar: escribe sus lecciones (máx. 2,500 caracteres)
20:17  foto de la cuenta y bitácora. Sin LLM.
```

**Pantalla de todo el mercado** (`bot/screener.py`, sección `screener` de `config.yaml`). En cada
despertar el código pide al screener de Alpaca las 50 que más suben, las 50 que más bajan y las 50
más activas por volumen de todo EE. UU. (mismas llaves). Quita warrants y símbolos raros, lo que no
se puede operar en Alpaca, lo de menos de $5 y lo de menos de $20M de volumen diario promedio
(20 días de Yahoo Finance). También quita ETFs, ETNs, fondos y productos apalancados o inversos
(por su nombre en Alpaca y una lista fija): solo acciones individuales. Ordena por |cambio de hoy| × volumen relativo (acotado entre 0.2x y 5x)
y le pasa al agente las 30 primeras. El LLM no lee miles de acciones: eso sería caro y ordenaría
mal. Los umbrales y el orden son una heurística, no un factor probado. En cada despertar el agente debe dar un veredicto (comprar, corto,
vigilar o descartar, con razón) sobre las 5 primeras con `review_screen`; si termina sin hacerlo, el
código se lo recuerda una vez. El veredicto no es una orden y se ve en el dashboard. Si el screener
falla, el despertar sigue sin pantalla y queda el aviso. Ninguna posición puede pasar de
`agent.max_position_pct` (15%) de la cuenta: lo bloquea el código.

`research` corre TradingAgents completo (analistas de mercado, sentimiento, noticias y
fundamentales, debate alcista/bajista, trader y comité de riesgo) y devuelve
Buy/Overweight/Hold/Underweight/Sell con el razonamiento. Es lo caro: máximo 2 por despertar.

**Lo único que el código le impide:**
- Operar fuera de paper: el cliente se niega a arrancar si no apunta a `paper-api.alpaca.markets`.
- Gastar más del tope (abajo).
- Mandar órdenes que Alpaca rechazaría. En pre y post-market solo acepta órdenes limitadas con
  `extended_hours`; un short necesita que la acción se pueda pedir prestada; una orden no puede
  voltear una posición de largo a corto. Si se equivoca, recibe el error y corrige.
- Antes de vender algo que tiene stop, el bot cancela el stop (si no, Alpaca rechaza la venta
  porque el stop "aparta" esas acciones) y se lo dice al agente.

Las noticias y reportes son texto de terceros. El prompt le dice que nunca siga instrucciones
que aparezcan ahí, y lo peor que podría pasar si una lo engaña es una orden en dinero falso.

## Lo que tienes que hacer tú (una sola vez)

Yo no puedo crear cuentas ni manejar tus llaves. Son cuatro pasos:

1. **Alpaca**: crea una cuenta en alpaca.markets, entra a *Paper Trading* y genera las API keys.
2. **Anthropic**: en platform.claude.com crea una API key y fija tu límite en
   *Settings → Spend limits*. Ese es el tope duro de verdad; el del bot es un segundo candado.
3. **GitHub**: crea un repo vacío y sube esta carpeta:
   ```bash
   cd paper-trader
   git init -b main && git add . && git commit -m "agente trader"
   git remote add origin https://github.com/TU_USUARIO/paper-trader.git
   git push -u origin main
   ```
4. **Secrets** del repo (*Settings → Secrets and variables → Actions → New repository secret*):
   `ANTHROPIC_API_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`. Nunca los pegues en un chat.

Primera prueba: *Actions → Agente trader → Run workflow*, con **dry_run** y **force**
marcados. El agente piensa de verdad (gasta LLM) pero sus órdenes no se envían. La primera
corrida tarda más porque instala todo; las siguientes reusan el entorno guardado.

## Cuánto cuesta

**LLM (tope de $20 al mes, `budget.monthly_usd`; el límite real es el menor entre este y tu crédito en Anthropic).** Cómo se respeta:
- Cada día recibe lo que queda del mes (menos 5% de colchón) entre los días hábiles que faltan.
- Cada despertar puede gastar lo del día **menos** lo que necesitan los despertares que
  faltan. Así el de las 4:08 no se come el día.
- Cada llamada pasa por un contador que corta en cuanto se llega al límite. Puede pasarse
  por el costo de una sola llamada.
- Sin presupuesto, el despertar se salta y queda registrado. Las órdenes y stops abiertos
  siguen vivos en Alpaca.
- Un test simula un mes completo de despertares e investigaciones y verifica que nunca se
  pasa del tope.

Estimación **sin verificar** (nunca corrió con el LLM real), con los precios de Haiku 5.5 de
`config.yaml` ($0.10 / $0.50 por millón de tokens de entrada / salida): un despertar de
~40 mil tokens de entrada cuesta ~$0.005, unos $3.40 al mes por 32 × 21 despertares. Una
investigación de TradingAgents, de $0.03 a $0.10. Con $20 alcanzarían los despertares y entre
150 y 500 investigaciones al mes. El dashboard te dirá el costo real desde el primer día.

**GitHub Actions.** Los repos públicos no pagan minutos; los privados tienen 2,000 gratis al
mes y GitHub redondea cada job al minuto. Si cada despertar tarda 2-3 minutos (**sin medir**),
672 despertares al mes son 1,350-2,000 minutos: justo en el límite. Tres salidas:
- Hacer el repo **público**: no hay llaves en él (están en Secrets), pero cualquiera verá las
  operaciones y lecciones del agente.
- Dejar que GitHub cobre el excedente ($0.006 por minuto: 300 minutos extra son $1.80).
  Por defecto el límite de gasto es $0 y los despertares simplemente se detienen.
- Usar el horario alternativo que está comentado en `.github/workflows/bot.yml`: pre y
  post-market cada hora y horario regular cada 30 minutos (23 despertares al día).

Revisa *Settings → Billing → Usage* después de la primera semana.

## Correos del agente

Llega un correo cuando un despertar envía órdenes, cuando algo falla (error, sin presupuesto,
faltan llaves) y en el último despertar del día, que trae además el resumen del día
(despertares, órdenes, investigaciones y gasto). Los despertares sin novedad no mandan nada.
Cada correo dice cuándo empezó y terminó el despertar, cuánto duró y cuánto costó en LLM.

El costo lo calcula el bot con los tokens y la tabla de precios de `config.yaml`; la cifra
oficial está en la consola de Anthropic. GitHub Actions no cobra porque el repo es público.

Para activarlo (se manda desde tu Gmail a ti mismo):
1. Activa la verificación en dos pasos de Google y crea una contraseña de aplicación en
   myaccount.google.com/apppasswords (Google la muestra una sola vez).
2. Secrets del repo: `GMAIL_USER` (tu dirección de Gmail) y `GMAIL_APP_PASSWORD` (esa
   contraseña). Opcional: `EMAIL_TO` si quieres recibirlo en otra dirección.

Sin esos secrets no se manda nada y el bot sigue igual. Si el correo falla, el despertar no falla.

## Limitaciones que debes conocer

- **Fuera de horario solo hay órdenes limitadas** y los stops no se activan: protegen de
  9:30 a 16:00. Una noticia a las 18:00 la ve el agente en su siguiente despertar, pero el
  stop no la frena.
- **Entre despertares no ve nada.** Lo que pase en esos 30 minutos solo lo atienden sus
  órdenes y stops ya puestos.
- **GitHub puede atrasar o saltarse despertares** cuando tiene mucha carga. Cada despertar
  lee el estado real de la cuenta, así que un salto no rompe nada.
- **Los precios de hoy vienen de Yahoo Finance** (barras de 5 minutos con pre y post-market,
  pueden ir atrasados). El plan gratis de datos de Alpaca solo trae el exchange IEX.
- **Alpaca paper no simula** slippage, impacto de mercado ni dividendos; fuera de horario
  real la liquidez es mucho menor de lo que el paper hace parecer.
- **Haiku es el modelo más barato.** Decide más rápido y barato, no mejor. Para probar otro,
  cambia `llm.trader_model` (el contador ya tiene los precios de Sonnet y Opus).

## Lo que dicen los datos

Todo esto está en `research/` y se puede repetir gratis. Precios de OpenBB, 119 acciones,
evaluado caminando hacia adelante del 7-ago-2024 al 12-nov-2026; costo de 2 pb por lado.

| Pregunta | Resultado | Qué hace el bot con eso |
|---|---|---|
| ¿Day-trading o mantener? | En SPY, la noche rinde +4.3 pb/día (t=2.3) y la sesión +3.2 (t=1.2). Cerrar todo cada día deja fuera más de la mitad. | El agente puede mantener posiciones de noche; el prompt no lo obliga a cerrar. |
| ¿El modelo Alpha158 + Ridge de Qlib elige bien? | Sus carteras top-5/10/20 contra el universo a pesos iguales: entre −2.2% y +10.8% al año, todas con t<0.5. | No se le da al agente. |
| ¿Y el momentum 12-1? | Top-10: +39% al año sobre el universo (t=1.7). Pero quitando las 15 acciones que hoy sabemos que ganaron (MU, PLTR, HOOD, AMD…), la ventaja cae a +2.3% (t=0.2). | Se le da como una señal más entre sus fuentes de ideas. También es la regla contra la que se le mide. |
| ¿Shorts? | Los 10 peor rankeados en corto: −39% al año contra el universo (t=−1.9). | Permitidos (lo pediste); el agente decide. Se apagan con `agent.allow_short: false`. |
| ¿Stops? | En el núcleo de momentum, un stop de 2 ATR bajó la ventaja de +39% a +13% al año; uno de 3 ATR, a +28%. | El agente decide si los pone. |
| ¿Apalancamiento? | 33 años de SPY con 6.5% de interés de margen: 1x crece 10.7% al año, 1.5x 11.3%, 2x 11.0%. La peor caída pasa de −55% a −76% y −90%. | Alpaca le da 2× de buying power; el agente decide cuánto usa. |

Sobre el momentum: Jegadeesh y Titman documentaron que comprar a los ganadores de los últimos
3 a 12 meses y vender a los perdedores rindió alrededor de 1% al mes entre 1965 y 1989. Daniel
y Moskowitz encontraron que esa estrategia sufre caídas raras pero muy fuertes, sobre todo
cuando el mercado rebota tras una crisis.

Contexto: en los estudios grandes sobre traders que operan seguido, la mayoría pierde. En
Brasil, 97% de quienes hicieron day-trading más de 300 días perdieron dinero (Chague,
De-Losso y Giovannetti, 2020).

### Corrección de datos

Cboe devolvió una fila en el feriado del 26-may-2025 que repite el viernes anterior sin ajustar
por splits (BKNG ×25, NFLX ×10). Inflaba cualquier promedio que la incluyera. El bot ahora
elimina fechas duplicadas así y avisa de saltos de más de 45% con volumen normal (HON −51% el
29-jun-2026 fue su escisión, no una caída). Todas las cifras de arriba ya están limpias.

## Dashboard

```bash
python3 dashboard/app.py --demo    # 20 días de ejemplo con precios reales
python3 dashboard/app.py           # datos reales (lo que el bot subió al repo)
```

Abre `http://127.0.0.1:8765`. No instala nada (Python 3.9+ y git). Es de solo lectura;
*Sincronizar* hace `git pull` del repo.

- **Cuenta contra el mercado**: el agente, la regla de momentum sin IA y SPY, base 100.
- **Gasto real en el LLM**: tope, costo por despertar y por investigación, quién se lleva el presupuesto.
- **El día del agente**: cada despertar con lo que dijo, sus órdenes con la razón que dio,
  sus investigaciones (con el reporte completo de TradingAgents) y los errores que corrigió.
- **Lo que el agente aprendió**: sus lecciones, tal como las escribió.
- **¿Pasaría la prueba con dinero real?**: descuenta costos estimados (deslizamiento por orden
  e interés de margen, supuestos en `evaluation` de `config.yaml`) y compara contra un criterio
  fijado de antemano: 63 días de mercado, ganarle a SPY después de costos y alfa con t ≥ 2.
  Cuenta desde `evaluation.start_date` (2026-11-19, primer día completo con la pantalla actual)
  y cobra `slippage_bps_outside_extra` adicional en acciones fuera del universo.
- **¿De dónde sale el resultado?**: beta contra SPY, la regla de momentum contra SPY, el agente
  contra la regla, Buy contra Sell de sus investigaciones y alfa, cada uno con su prueba
  estadística. Dice "muestra chica" mientras no haya datos suficientes.
- Posiciones (con su stop), operaciones cerradas y órdenes con su razón.

En la demo el agente es un guion de reglas fijas, no el LLM: sirve para ver el tablero, no
dice nada de cómo operará el agente real.

### Dashboard en la web (GitHub Pages)

El mismo tablero como página web, en `https://TU_USUARIO.github.io/paper-trader/`. Después
de cada despertar, el workflow arma la página con el estado nuevo y la publica (tarda ~1-2
minutos más); la página abierta se vuelve a leer sola cada minuto. "En vivo" quiere decir que
ves cada despertar poco después de que pasa. Entre despertares no hay nada nuevo que ver,
porque el agente no está mirando.

Para activarla:
1. *Settings → Pages → Build and deployment → Source*: **GitHub Actions**.
2. *Settings → Secrets and variables → Actions → Variables*: crea `PUBLISH_DASHBOARD` = `true`.
3. Corre un despertar a mano (*Run workflow*) o espera el siguiente.

Antes de activarla, ten en cuenta:
- **La página es pública en internet.** Con GitHub Free, Pages solo funciona si el repo es
  público; con Pro el repo puede ser privado, pero la página sigue siendo pública. No
  contiene llaves (esas viven en Secrets), pero sí las operaciones, el saldo de la cuenta
  paper, los razonamientos y las lecciones del agente. Lleva `noindex` para que los
  buscadores no la listen, pero cualquiera con el enlace puede abrirla.
- Con repo público los minutos de Actions son gratis, así que el job extra no cuesta.
- Sin `PUBLISH_DASHBOARD`, el job de publicar no corre y todo sigue igual.

Para armarla en tu máquina sin publicarla: `python3 dashboard/app.py --export site`.

## Lo que no está probado

Probé todo lo que se puede sin llaves: 46 tests (incluye un mes completo de despertares contra
el tope y que el modelo real acepta las herramientas), OpenBB y Qlib con datos reales,
TradingAgents construido con el modelo configurado, y la demo de 20 días. **Nunca corrió una
llamada real al LLM ni una orden real a Alpaca.** Qué vigilar la primera semana:

- Cuánto cuesta y cuánto tarda un despertar y una investigación (dashboard y Actions).
- Que Yahoo Finance responda desde GitHub (precios de hoy y noticias).
- Que el agente use bien las órdenes limitadas fuera de horario. Si repite errores, lo verás
  en el dashboard en amarillo.
- Que TradingAgents acepte `claude-haiku-5-5` (no está en su menú; avisa pero continúa).
- El analista `social` usa StockTwits y Reddit. Como Reddit bloquea a GitHub (403), recibe de
  ApeWisdom el conteo de menciones en Reddit (atención, no opinión).

## Cambiar cosas

Todo está en `config.yaml`: tope, modelo, horario y frecuencia (`agent.tick_minutes` debe
coincidir con el cron del workflow), vueltas por despertar, investigaciones por despertar,
cortos, universo y tamaño de la lista de vigilancia. Quien despierta al agente es `clock.yml` ("Reloj del agente"): una cadena de corridas que
lanza cada despertar y se releva sola cada ~5 h; no depende del cron de GitHub. Para pausar
al agente, cancela la corrida en curso del reloj; para reanudar, *Run workflow* en el reloj.
El cron de `bot.yml` queda solo de respaldo y está en UTC
(GitHub no lanzó los despertares cuando se usó el campo `timezone`); el propio job descarta
los que caen fuera de 4:00-20:00 de Nueva York. El prompt del agente está en
`bot/trader.py` (`SYSTEM`). Para pausar: *Actions → Agente trader → ⋯ → Disable workflow*.

## Correrlo en tu máquina (opcional)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock        # Linux; en Mac usa requirements.txt
python -m pytest tests
python -m bot.tick --demo               # regenera la demo (sin llaves ni LLM)
python -m research.swing                # repite las pruebas de datos (gratis)
```

Versiones fijadas: TradingAgents al commit `9fa1196` (escaneado el 2026-11-15), OpenBB core
2.0.1 con los proveedores Cboe y Nasdaq, Qlib 0.9.7, alpaca-py 0.45.0, langchain-anthropic
1.7.10. Requiere Python 3.12.
