# Arithmetische und geometrische Folgen

## 1. Ziel des Kapitels

Eine Folge durch ihre Glieder und durch ihr allgemeines Glied beschreiben, eine arithmetische oder eine geometrische Folge erkennen, ein beliebiges Glied und die Summe der ersten Glieder jeder Art bestimmen und entscheiden, welche Art eine Liste von Gliedern hat.

### Was der Test verlangt

| Art | Erwartet |
|---|---|
| Definitionen zum Wiedergeben | Folge, arithmetische Folge, Differenz, geometrische Folge, Quotient |
| Verfahren | $a_n$ aus $a_1$ und $d$ oder $q$ bestimmen; $d$ aus zwei Gliedern bestimmen; Summe der ersten $n$ Glieder; entscheiden, ob eine Folge arithmetisch, geometrisch oder keins von beiden ist |
| Problemaufgaben | eine Situation, die sich als arithmetisch oder geometrisch erweist (gestapelte Reihen, Verdopplung) |

## 2. Vorwissen

- Potenzen mit ganzzahligen Exponenten.
- Eine lineare Gleichung lösen.
- Einen Punkt $P(x \mid y)$ im Koordinatensystem ablesen.

## 3. Schreibweisen und Konventionen

- Dezimalkomma: `0,5`, in LaTeX $0{,}5$.
- Eine Folge wird $(a_n)$ geschrieben; ihre Glieder sind $a_1, a_2, a_3, \dots$: **das erste Glied ist $a_1$**, nie $a_0$. Beispiel: $a_1 = 5$.
- Differenz einer arithmetischen Folge: $d$. Quotient einer geometrischen Folge: $q$. Summe der ersten $n$ Glieder: $s_n$.
- Mengen in geschweiften Klammern, Elemente durch Semikolon getrennt: `{2; 5}`.
- Graphen: Eine Folge wird als einzelne Punkte $(n \mid a_n)$ gezeichnet, mit $n$ auf der waagerechten Achse und $a_n$ auf der senkrechten Achse; die Punkte werden nie durch eine Linie verbunden.

## 4. Begriffe in didaktischer Reihenfolge

### 4.1 Folgen

> Eine Folge ist eine Liste von Zahlen in einer festen Reihenfolge: $a_1, a_2, a_3, \dots$ Die Zahl $a_n$ ist das Glied mit der Nummer $n$.

Eine Folge kann durch eine Formel für $a_n$ (das allgemeine Glied) oder durch eine Vorschrift gegeben sein, die von einem Glied zum nächsten führt.

**Beispiele aus dem Kurs**: $a_n = 3n - 2$ ergibt $a_1 = 1$, $a_2 = 4$, $a_3 = 7$.

**Grafische Darstellung**: Graph von $a_n = 3n - 2$, einzelne Punkte $(1 \mid 1)$, $(2 \mid 4)$, $(3 \mid 7)$, $(4 \mid 10)$, $(5 \mid 13)$, $(6 \mid 16)$.

### 4.2 Arithmetische Folgen

> Eine Folge ist arithmetisch, wenn jedes Glied aus dem vorherigen entsteht, indem man dieselbe Zahl $d$ addiert, die Differenz genannt wird: $a_{n+1} = a_n + d$.

- Allgemeines Glied: $a_n = a_1 + (n - 1)\,d$.
- Summe der ersten $n$ Glieder: $s_n = \dfrac{n\,(a_1 + a_n)}{2}$.

**Beispiele aus dem Kurs**: $a_1 = 5$ und $d = 3$: $a_{10} = 5 + 9 \cdot 3 = 32$ und $s_{10} = \dfrac{10\,(5 + 32)}{2} = 185$.

**Typische Fehler**: $a_n = a_1 + n\,d$ schreiben (die Anzahl der Schritte von $a_1$ bis $a_n$ ist $n - 1$).

### 4.3 Geometrische Folgen

> Eine Folge ist geometrisch, wenn jedes Glied aus dem vorherigen entsteht, indem man mit derselben Zahl $q$ multipliziert, die Quotient genannt wird: $a_{n+1} = q \cdot a_n$.

- Allgemeines Glied: $a_n = a_1 \cdot q^{\,n-1}$.
- Summe der ersten $n$ Glieder: $s_n = a_1 \cdot \dfrac{1 - q^n}{1 - q}$. Bedingung: $q \neq 1$.

**Beispiele aus dem Kurs**: $a_1 = 2$ und $q = 3$: $a_5 = 2 \cdot 3^4 = 162$ und $s_5 = 2 \cdot \dfrac{1 - 3^5}{1 - 3} = 242$.

### 4.4 Welche Art von Folge?

Verfahren:
1. Berechne die Differenzen $a_2 - a_1$, $a_3 - a_2$, $a_4 - a_3$. Sind sie alle gleich, ist die Folge arithmetisch und $d$ ist diese Differenz.
2. Wenn nicht, berechne die Quotienten $\dfrac{a_2}{a_1}$, $\dfrac{a_3}{a_2}$, $\dfrac{a_4}{a_3}$. Sind sie alle gleich, ist die Folge geometrisch und $q$ ist dieser Quotient.
3. Trifft keins von beiden zu, ist die Folge weder arithmetisch noch geometrisch.

**Beispiele aus dem Kurs**: $3 ; 6 ; 12 ; 24$: Die Differenzen $3 ; 6 ; 12$ sind nicht gleich, die Quotienten $2 ; 2 ; 2$ schon: geometrisch mit $q = 2$. $7 ; 4 ; 1 ; -2$: Die Differenzen sind alle $-3$: arithmetisch mit $d = -3$.

**Typische Fehler**: nur die ersten beiden Glieder prüfen.

## 5. Fachwortschatz

**Wörter des Kurses, zu verwenden**: Folge, Glied, Nummer, allgemeines Glied, arithmetische Folge, Differenz, geometrische Folge, Quotient, Summe der ersten $n$ Glieder.

**Nicht einzuführende Wörter**: Nichts im Material.

## 6. Typische Aufgaben

### 6.1 Arithmetische Folgen

#### 6.1.1

**Eine arithmetische Folge hat $a_1 = 4$ und $d = 5$. Bestimme $a_{12}$ und $s_{12}$.**
**Verfahren:** $a_n = a_1 + (n - 1)\,d$, dann $s_n = \frac{n\,(a_1 + a_n)}{2}$.
**Antwort:** $a_{12} = 4 + 11 \cdot 5 = 59$ und $s_{12} = \frac{12\,(4 + 59)}{2} = 378$.

#### 6.1.2

**Eine arithmetische Folge hat $a_3 = 11$ und $a_7 = 23$. Bestimme $d$ und $a_1$.**
**Verfahren:** Vier Schritte trennen $a_3$ von $a_7$, also $4d = a_7 - a_3$; dann von $a_3$ aus zurückgehen.
**Antwort:** $d = \frac{23 - 11}{4} = 3$ und $a_1 = 11 - 2 \cdot 3 = 5$.

### 6.2 Geometrische Folgen

#### 6.2.1

**Eine geometrische Folge hat $a_1 = 3$ und $q = 2$. Bestimme $a_8$.**
**Verfahren:** $a_n = a_1 \cdot q^{\,n-1}$.
**Antwort:** $a_8 = 3 \cdot 2^7 = 384$.

#### 6.2.2

**Eine geometrische Folge hat $a_1 = 1000$ und $q = 0{,}5$. Bestimme $a_4$ und $s_4$.**
**Verfahren:** allgemeines Glied, dann die Summenformel mit $q \neq 1$.
**Antwort:** $a_4 = 1000 \cdot 0{,}5^3 = 125$ und $s_4 = 1000 \cdot \frac{1 - 0{,}5^4}{1 - 0{,}5} = 1875$.

### 6.3 Welche Art von Folge?

#### 6.3.1

**Entscheide, welche Art diese Folge hat: $2 ; 6 ; 18 ; 54$.**
**Verfahren:** Differenzen, dann Quotienten.
**Antwort:** Die Differenzen $4 ; 12 ; 36$ sind nicht gleich; die Quotienten sind alle $3$: geometrisch mit $q = 3$.

#### 6.3.2

**Entscheide, welche Art diese Folge hat: $20 ; 17 ; 14 ; 11$.**
**Verfahren:** Differenzen, dann Quotienten.
**Antwort:** Die Differenzen sind alle $-3$: arithmetisch mit $d = -3$.

#### 6.3.3

**Entscheide, welche Art diese Folge hat: $1 ; 4 ; 9 ; 16$.**
**Verfahren:** Differenzen, dann Quotienten.
**Antwort:** Die Differenzen $3 ; 5 ; 7$ sind nicht gleich und die Quotienten $4 ; 2{,}25 ; \dots$ sind nicht gleich: keins von beiden.

#### 6.3.4

**Schreib die ersten vier Glieder von $a_n = 2n + 1$ auf und gib an, welche Art von Folge es ist.**
**Verfahren:** $a_1, \dots, a_4$ berechnen und dann das Verfahren aus § 4.4 anwenden.
**Antwort:** im Material nicht korrigiert

### 6.4 Problemaufgaben

#### 6.4.1

**Ein Stapel Baumstämme hat 12 Stämme in der untersten Reihe, und jede Reihe hat einen Stamm weniger als die Reihe darunter. Es gibt 8 Reihen. Wie viele Stämme hat der Stapel?**
**Verfahren:** Die Reihen bilden eine arithmetische Folge mit $a_1 = 12$ und $d = -1$; die 8 Glieder addieren.
**Antwort:** $a_8 = 12 - 7 = 5$ und $s_8 = \frac{8\,(12 + 5)}{2} = 68$ Stämme.

#### 6.4.2

**Eine Bakterienkultur hat anfangs 500 Bakterien, und ihre Anzahl verdoppelt sich jede Stunde. Wie viele Bakterien sind es nach 4 Stunden?**
**Verfahren:** $a_1 = 500$ ist die Anzahl am Anfang, also ist die Anzahl nach 4 Stunden $a_5$; geometrische Folge mit $q = 2$.
**Antwort:** $a_5 = 500 \cdot 2^4 = 8000$ Bakterien.

## 7. Zu prüfende Punkte

Keine.
