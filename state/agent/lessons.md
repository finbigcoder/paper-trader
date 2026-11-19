LECCIONES (revisadas 18-nov-2026, después de 3 días sin una sola operación)

El problema principal: en 73 despertares no abrí ninguna posición. Mis niveles de entrada estaban lejos del precio (TXN a 284 con el precio en ~290, TGT a 162 con ~169) y nunca dejé órdenes en ellos, porque creía que una orden llenada entre despertares quedaba sin supervisión. Eso ya no es cierto: place_order con stop_price deja la entrada y su stop juntos en Alpaca (OTO, GTC). No operar no es neutral: con la cuenta en efectivo, cualquier día que SPY sube voy perdiendo contra él.

Qué funcionó:
- No perseguir precios de pre/post-market sin volumen (MDLN 39.69 en post).
- Definir disparador y stop antes de entrar.
- Desconfiar de datos anómalos (AES con 10.7x de volumen y +0.3% de cambio). HON ya viene ajustado por la escisión del 29-jun.

Qué haré distinto:
1. Si tengo un nivel de entrada con stop, dejo la orden limitada en ese nivel con stop_price en el mismo despertar. No espero a despertar justo cuando el precio llegue.
2. Niveles a menos de ~1 ATR del precio. Si mi nivel está más lejos, no es un plan para hoy.
3. Rupturas (como MDLN sobre 39.3): si en un despertar regular veo la ruptura confirmada con volumen, entro ahí mismo con stop.
4. Riesgo por operación: 0.5-1% de la cuenta entre entrada y stop. Con riesgo chico puedo tener 3-5 posiciones a la vez. No tengo que elegir un solo nombre por sesión.
5. Cada operación lleva disparador, stop, tamaño y horizonte. Si falta uno lo completo; no descarto el nombre por eso.
6. Resultados (TGT, TJX, BRBR): un gap con volumen que aguanta la primera hora es un setup válido; el stop va bajo el mínimo de la primera hora.
7. En post-market, sin cambios relevantes: una línea "sin cambios" y nada más. La pantalla completa se revisa en serio una vez por sesión.
