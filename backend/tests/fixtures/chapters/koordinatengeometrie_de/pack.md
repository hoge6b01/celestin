# Koordinatengeometrie in der Ebene

## 1. Ziel des Kapitels

Punkte in einem kartesischen Koordinatensystem angeben, den Mittelpunkt einer Strecke und den Abstand zweier Punkte bestimmen, die Gleichung einer Geraden aufstellen, parallele oder orthogonale Geraden erkennen und den Schnittpunkt zweier Geraden bestimmen.

### Was der Test verlangt

| Art | Erwartet |
|---|---|
| Definitionen zum Wiedergeben | kartesisches Koordinatensystem, parallele Geraden, orthogonale Geraden |
| Verfahren | Mittelpunkt einer Strecke, Abstand zweier Punkte, Gleichung der Geraden durch zwei Punkte, Schnittpunkt zweier Geraden |
| Erkennen | parallele oder orthogonale Geraden, rechtwinkliges Dreieck |

## 2. Vorwissen

- Der Satz des Pythagoras.
- Eine lineare Gleichung lösen.
- Rechnen mit Brüchen.

## 3. Schreibweisen und Konventionen

- Dezimalkomma: `4,5`, in LaTeX $4{,}5$.
- Koordinaten eines Punktes: zuerst die $x$-Koordinate, dann die $y$-Koordinate, getrennt durch einen senkrechten Strich: `A(2 | 3)`, in LaTeX $A(2 \mid 3)$.
- Strecke $\overline{AB}$, Gerade $AB$, Länge der Strecke $|AB|$.
- Gleichung einer Geraden: `g: y = mx + b`, wobei `m` die Steigung und `b` der $y$-Achsenabschnitt ist.
- Figuren: in einem kartesischen Koordinatensystem; Punkte mit einem Kreuz markiert und mit einem Großbuchstaben benannt; ein rechter Winkel mit einem kleinen Quadrat markiert; gleich lange Strecken mit gleich vielen Strichen markiert.

## 4. Begriffe in didaktischer Reihenfolge

### 4.1 Kartesisches Koordinatensystem und Koordinaten

> Ein Koordinatensystem ist kartesisch, wenn seine Achsen senkrecht zueinander stehen und dieselbe Einheit haben.

Jeder Punkt der Ebene wird durch seine Koordinaten angegeben: seine $x$-Koordinate, auf der waagerechten Achse abgelesen, dann seine $y$-Koordinate, auf der senkrechten Achse abgelesen.

**Beispiele aus dem Kurs**: $A(1 \mid 1)$, $B(3 \mid 4)$ und $C(6 \mid 2)$.

**Grafische Darstellung**: kartesisches Koordinatensystem, die Punkte A, B und C mit einem Kreuz markiert.

### 4.2 Mittelpunkt und Abstand

- Mittelpunkt $M$ der Strecke $\overline{AB}$: $M\left(\dfrac{x_A + x_B}{2} \mid \dfrac{y_A + y_B}{2}\right)$.
- Abstand von $A$ und $B$: $|AB| = \sqrt{(x_B - x_A)^2 + (y_B - y_A)^2}$.

**Beispiele aus dem Kurs**: Der Mittelpunkt von $\overline{AC}$ ist $M(3{,}5 \mid 1{,}5)$ ; $|AB| = \sqrt{2^2 + 3^2} = \sqrt{13}$ und $|BC| = \sqrt{3^2 + (-2)^2} = \sqrt{13}$.

### 4.3 Gleichung einer Geraden

> Eine Gerade, die nicht parallel zur senkrechten Achse ist, hat eine Gleichung der Form $y = mx + b$; $m$ ist ihre Steigung und $b$ ihr $y$-Achsenabschnitt.

- Steigung der Geraden $AB$: $m = \dfrac{y_B - y_A}{x_B - x_A}$.
- Um $b$ zu bestimmen, setzt man für $x$ und $y$ die Koordinaten eines Punktes der Geraden ein.

**Beispiele aus dem Kurs**: die Gerade $AB$, mit $A(1 \mid 1)$ und $B(3 \mid 4)$: $m = \dfrac{4 - 1}{3 - 1} = \dfrac{3}{2}$ ; $1 = \dfrac{3}{2} \cdot 1 + b$, also $b = -\dfrac{1}{2}$ und $AB: y = \dfrac{3}{2}x - \dfrac{1}{2}$.

### 4.4 Parallele und orthogonale Geraden

> Zwei Geraden sind parallel, wenn sie dieselbe Steigung haben.

> Zwei Geraden sind orthogonal, wenn das Produkt ihrer Steigungen $-1$ ist.

**Beispiele aus dem Kurs**: Das Dreieck $ABC$ hat einen rechten Winkel bei $B$: $m_{AB} = \dfrac{3}{2}$, $m_{BC} = \dfrac{2 - 4}{6 - 3} = -\dfrac{2}{3}$ und $\dfrac{3}{2} \cdot \left(-\dfrac{2}{3}\right) = -1$. Es ist auch gleichschenklig: $|AB| = |BC| = \sqrt{13}$.

**Grafische Darstellung**: in einem kartesischen Koordinatensystem das Dreieck $ABC$ mit $A(1 \mid 1)$, $B(3 \mid 4)$ und $C(6 \mid 2)$, die Punkte mit einem Kreuz markiert, der rechte Winkel bei $B$ mit einem kleinen Quadrat markiert, $\overline{AB}$ und $\overline{BC}$ mit einem Strich markiert.

### 4.5 Schnittpunkt zweier Geraden

Der Schnittpunkt zweier Geraden, die sich schneiden, liegt auf beiden Geraden: Seine Koordinaten erfüllen beide Gleichungen. Setze die beiden Terme für $y$ gleich, um $x$ zu bestimmen, und berechne dann $y$.

**Beispiele aus dem Kurs**: $g_1: y = 2x - 3$ und $g_2: y = -x + 6$: $2x - 3 = -x + 6$, also $3x = 9$ und $x = 3$ ; $y = 2 \cdot 3 - 3 = 3$. Der Schnittpunkt ist $S(3 \mid 3)$.

**Grafische Darstellung**: in einem kartesischen Koordinatensystem die Geraden $g_1$ und $g_2$ und ihr Schnittpunkt $S$, mit einem Kreuz markiert.

## 5. Fachwortschatz

**Wörter des Kurses, zu verwenden**: kartesisches Koordinatensystem, $x$-Koordinate, $y$-Koordinate, Koordinaten, Mittelpunkt, Abstand, Steigung, $y$-Achsenabschnitt, parallele Geraden, orthogonale Geraden, Schnittpunkt, rechtwinkliges Dreieck, gleichschenkliges Dreieck.

**Nicht einzuführende Wörter**: Nichts im Material.

## 6. Typische Aufgaben

### 6.1 Mittelpunkt, Abstand und rechtwinkliges Dreieck

#### 6.1.1

**Gegeben sind $A(-1 \mid -2)$ und $B(4 \mid 10)$. Bestimme die Koordinaten des Mittelpunkts $M$ von $\overline{AB}$ und den Abstand $|AB|$.**
**Verfahren:** die Formeln für den Mittelpunkt und den Abstand.
**Antwort:** $M(1{,}5 \mid 4)$ ; $|AB| = \sqrt{5^2 + 12^2} = 13$.

#### 6.1.2

**Zeige, dass das Dreieck $PQR$ mit $P(0 \mid 2)$, $Q(6 \mid 4)$ und $R(4 \mid 10)$ einen rechten Winkel hat.**
**Verfahren:** die Steigungen der Seiten bestimmen; zwei Seiten sind orthogonal, wenn das Produkt ihrer Steigungen $-1$ ist.
**Antwort:** $m_{PQ} = \frac{1}{3}$ und $m_{QR} = -3$ ; ihr Produkt ist $-1$: Das Dreieck $PQR$ hat einen rechten Winkel bei $Q$.

### 6.2 Geraden

#### 6.2.1

**Bestimme die Gleichung der Geraden $g$ durch $A(2 \mid 1)$ und $B(4 \mid 7)$.**
**Verfahren:** $m = \frac{y_B - y_A}{x_B - x_A}$, dann $b$ mit den Koordinaten von $A$.
**Antwort:** $m = 3$ und $b = -5$: $g: y = 3x - 5$.

#### 6.2.2

**Bestimme den Schnittpunkt der Geraden $g_1: y = 4x - 3$ und $g_2: y = -2x + 9$.**
**Verfahren:** die beiden Terme für $y$ gleichsetzen, dann $y$ berechnen.
**Antwort:** $4x - 3 = -2x + 9$, also $6x = 12$ und $x = 2$ ; $y = 5$: $S(2 \mid 5)$.

#### 6.2.3

**Sind die Geraden $g: y = \frac{1}{2}x + 3$ und $h: y = -2x + 1$ parallel, orthogonal oder keins von beiden?**
**Verfahren:** die Steigungen vergleichen, dann ihr Produkt berechnen.
**Antwort:** $\frac{1}{2} \cdot (-2) = -1$: Sie sind orthogonal.

## 7. Zu prüfende Punkte

Keine.
