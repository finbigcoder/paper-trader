Lecciones (actualizadas 23-nov-2026, cierre post-market; SPY +4.9%, cuenta -$1,128 hoy por el corto NVDA ya cerrado y el gap en contra; valor $97,994)

Estado de cierre: única posición PDD largo 80 @86.74 (último ~87.0, +$29) con venta stop 82.0 activa (490255a2). Orden abierta fc517ea4: compra 85 NVDA límite 163.5 sin llenar, con stop 158 NO adjunto (en post-market Alpaca no adjunta el stop). Las lecciones de 20-nov sobre NVDA corto 40 y su stop 137.5 ya no aplican: esa posición no aparece en la cuenta.

Qué funcionó:
- Stop de PDD en 82.0 activo, sin promediar ni reentrar.
- No perseguir CRWV ni NVDA después del gap: CRWV superó mi disparador de 41.5 sin setup y quedó descartado.
- Pantalla evaluada en cada despertar, con veredicto por nombre.

Qué no funcionó:
- Repetí notas de post-market casi idénticas de 16:08 a 19:38 (más de 10 veces). Gasté presupuesto sin aportar información. Un "sin cambios" de una línea basta.
- La compra NVDA a 163.5 quedó casi 1.5% debajo de un precio de 165-167 tras un gap de +32%: una orden pasiva que puede no llenarse nunca. Si quiero NVDA, la entrada tiene que estar en un nivel que pueda tocarse en la sesión regular, con stop adjunto desde el inicio.
- Dejé la orden de NVDA con un stop que no se adjunta en post-market. Eso crea un hueco de horas si se llena en pre-market o al abrir. Si la orden no tiene stop adjunto, no la dejo viva sin plan.
- Mantuve la misma tesis SMCI (disparador 25) varios despertares sin cambio de datos.

Qué haré distinto:
1. Primer paso en regular (9:30): consultar órdenes y posiciones antes de cualquier análisis. Si fc517ea4 se llenó, poner set_stop 158 de inmediato y verificar que quede activo.
2. Toda entrada nueva en regular con stop_price (OTO). En post-market, solo límite con stop anotado para ponerlo al despertar regular.
3. Niveles de entrada a menos de ~1 ATR del último precio. Después de un gap grande, esperar confirmación en regular, no poner límites pasivos bajo el mercado.
4. Riesgo por operación 0.5-1% de la cuenta; tamaño = riesgo / distancia al stop.
5. Antes de una posición nueva, tesis escrita: disparador, stop, tamaño, horizonte.
6. Condiciones precisas y medibles ("una hora regular cierra sobre 25 con volumen"), no "rebota" ni "parece".
7. Un día de SPY fuerte no es disparador por sí mismo; cada nombre necesita su propio setup.
8. No repetir el mismo análisis sin decidir: si no hay cambio de datos, la nota es de una línea.

Vigilancia para mañana en regular:
- Stops: PDD 82.0 (s