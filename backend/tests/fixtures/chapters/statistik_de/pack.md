# Beschreibende Statistik mit einem Merkmal

## 1. Ziel des Kapitels

Die Art eines Merkmals erkennen, das passende Diagramm wählen und ablesen (Kreisdiagramm, Säulendiagramm, Histogramm, Summenhäufigkeitspolygon) und das arithmetische Mittel, den Median, den Modalwert und die Quartile einer Datenreihe berechnen, mit dem Boxplot.

### Was der Test verlangt

| Art | Erwartet |
|---|---|
| Definitionen zum Wiedergeben | Grundgesamtheit, Merkmalsträger, Stichprobe, Merkmal, relative Häufigkeit |
| Verfahren | Winkel eines Kreisausschnitts im Kreisdiagramm; Höhe eines Rechtecks im Histogramm bei Klassen unterschiedlicher Klassenbreite; kumulierte Häufigkeiten; arithmetisches Mittel, Median, Modalwert, $Q_1$ und $Q_3$ |
| Erkennen | die Art eines Merkmals und das passende Diagramm |
| Diagramme zum Zeichnen | Säulendiagramm mit Häufigkeitspolygon, Histogramm, Summenhäufigkeitspolygon, Boxplot |

## 2. Vorwissen

- Brüche, Prozente und Dezimalzahlen.
- Punkte im Koordinatensystem ablesen und eintragen.
- Zahlen ordnen.

## 3. Schreibweisen und Konventionen

- Dezimalkomma: `2,125`, in LaTeX $2{,}125$.
- Klassen enthalten ihre linke Grenze und schließen ihre rechte Grenze aus: `[10 ; 20[`.
- Gesamtzahl $N$, absolute Häufigkeit $H$, relative Häufigkeit $h = H / N$, geschrieben als Dezimalzahl (`0,25`) oder in Prozent (`25 %`).
- Arithmetisches Mittel $\bar{x}$, Median $M$, Quartile $Q_1$ und $Q_3$.
- Grafische Darstellungen:
  - „Kreisdiagramm“ für ein qualitatives Merkmal, Winkel = (absolute Häufigkeit / $N$) · 360°;
  - „Säulendiagramm“ für ein diskretes Merkmal, Werte auf der waagerechten Achse, absolute Häufigkeiten auf der senkrechten Achse; das „Häufigkeitspolygon“ verbindet die oberen Enden der Säulen;
  - „Histogramm“ für ein stetiges Merkmal, Flächeninhalt proportional zur absoluten Häufigkeit; Klassen unterschiedlicher Klassenbreite werden auf eine Bezugsbreite umgerechnet (Höhe = absolute Häufigkeit · Bezugsbreite / Klassenbreite);
  - „Summenhäufigkeitspolygon“, Punkte an den oberen Klassengrenzen, beginnend mit 0 an der unteren Grenze der ersten Klasse;
  - „Boxplot“, waagerecht, von $Q_1$ bis $Q_3$ durch den Median geteilt, mit Whiskern bis zum Minimum und zum Maximum.

## 4. Begriffe in didaktischer Reihenfolge

### 4.1 Grundgesamtheit, Merkmalsträger, Stichprobe

> Die Grundgesamtheit ist die Menge aller Merkmalsträger, auf die sich eine Untersuchung bezieht.

> Ein Merkmalsträger ist ein einzelnes Element der Grundgesamtheit.

> Eine Stichprobe ist ein Teil der Grundgesamtheit, der tatsächlich beobachtet wird.

**Grafische Darstellung**: Mengendiagramm mit ineinanderliegenden Mengen: Die Menge „Grundgesamtheit“ enthält die Menge „Stichprobe“, ein Kreuz „Merkmalsträger“ innerhalb der Stichprobe.

### 4.2 Merkmal

> Die Eigenschaft, die untersucht wird, heißt das Merkmal.

- Qualitativ: Seine Ausprägungen sind keine Zahlen (Farbe, Lieblingssport).
- Quantitativ diskret: Es nimmt nur einzelne Werte an (Anzahl der Bücher, Schuhgröße).
- Quantitativ stetig: Es kann jeden Wert eines Intervalls annehmen (Körpergröße, Masse, Zeit); die Werte werden in Klassen $[a ; b[$ zusammengefasst.

### 4.3 Absolute und relative Häufigkeit

Die absolute Häufigkeit eines Wertes ist die Anzahl der Merkmalsträger mit diesem Wert; die Gesamtzahl ist $N$. Die relative Häufigkeit ist $h = \dfrac{H}{N}$, geschrieben als Dezimalzahl ($0{,}25$) oder in Prozent ($25\,\%$).

### 4.4 Ein qualitatives Merkmal darstellen

**Beispiele aus dem Kurs**: Lieblingssport von 40 Schülerinnen und Schülern: Fußball 14, Basketball 10, Schwimmen 8, Tennis 8. Winkel eines Kreisausschnitts: $\dfrac{\text{absolute Häufigkeit}}{N} \cdot 360°$.

**Grafische Darstellung**: Kreisdiagramm, Kreisausschnitte Fußball 126°, Basketball 90°, Schwimmen 72°, Tennis 72°.

### 4.5 Ein diskretes Merkmal darstellen

**Beispiele aus dem Kurs**: Anzahl der Bücher, die 24 Schülerinnen und Schüler im letzten Monat gelesen haben: 0 → 3, 1 → 5, 2 → 7, 3 → 5, 4 → 3, 5 → 1.

**Grafische Darstellung**: Säulendiagramm, Achse „Gelesene Bücher“, Achse „Absolute Häufigkeit“, Säulen 0 → 3, 1 → 5, 2 → 7, 3 → 5, 4 → 3, 5 → 1, mit dem Häufigkeitspolygon.

### 4.6 Ein stetiges Merkmal darstellen

**Beispiele aus dem Kurs**: täglicher Schulweg von 50 Schülerinnen und Schülern: $[0 ; 10[$: 5 ; $[10 ; 20[$: 10 ; $[20 ; 30[$: 15 ; $[30 ; 50[$: 12 ; $[50 ; 90[$: 8.

Die Rechtecke grenzen aneinander, eines pro Klasse; der Flächeninhalt eines Rechtecks ist proportional zur absoluten Häufigkeit. Bei Klassen unterschiedlicher Klassenbreite nimmt der Kurs eine Bezugsbreite (hier 10 Minuten): Höhe $= \dfrac{\text{absolute Häufigkeit} \cdot 10}{\text{Klassenbreite}}$.

**Grafische Darstellung**: Histogramm, Achse „Schulweg (min)“ mit den Werten 0, 10, 20, 30, 50, 90, Achse „Absolute Häufigkeit pro 10 Minuten“, Höhen 5 ; 10 ; 15 ; 6 ; 2.

### 4.7 Kumulierte Häufigkeiten

Die kumulierte Häufigkeit einer Klasse ist die Summe ihrer absoluten Häufigkeit und der absoluten Häufigkeiten der Klassen davor.

**Beispiele aus dem Kurs**: Schulwege: 5 ; 15 ; 30 ; 42 ; 50, also sind die kumulierten relativen Häufigkeiten 10 % ; 30 % ; 60 % ; 84 % ; 100 %.

**Grafische Darstellung**: Summenhäufigkeitspolygon, Punkte $(0 \mid 0)$, $(10 \mid 10)$, $(20 \mid 30)$, $(30 \mid 60)$, $(50 \mid 84)$, $(90 \mid 100)$, senkrechte Achse in %.

### 4.8 Modalwert, arithmetisches Mittel und Median

- Modalwert: der Wert mit der größten absoluten Häufigkeit; bei einem stetigen Merkmal die Modalklasse.
- Arithmetisches Mittel: $\bar{x} = \dfrac{H_1 x_1 + H_2 x_2 + \dots + H_k x_k}{N}$. Bei einem stetigen Merkmal ist $x_i$ die Klassenmitte jeder Klasse.
- Median $M$: Er teilt die geordneten Daten in zwei gleich große Gruppen. Ist $N$ ungerade, ist er der Wert an der Stelle $\frac{N+1}{2}$; ist $N$ gerade, ist er der Mittelwert der Werte an den Stellen $\frac{N}{2}$ und $\frac{N}{2} + 1$.

**Beispiele aus dem Kurs**: Bücher: Modalwert 2 ; $\bar{x} = \dfrac{51}{24} = 2{,}125$ ; $M = 2$.

### 4.9 Quartile und Boxplot

> Das erste Quartil $Q_1$ ist der kleinste Wert der Datenreihe, für den mindestens 25 % der Werte kleiner oder gleich diesem Wert sind. Das dritte Quartil $Q_3$ ist der kleinste Wert, für den mindestens 75 % der Werte kleiner oder gleich diesem Wert sind.

**Beispiele aus dem Kurs**: Bücher: $Q_1 = 1$ ; $Q_3 = 3$.

**Grafische Darstellung**: waagerechter Boxplot, Minimum 0, $Q_1$ 1, Median 2, $Q_3$ 3, Maximum 5.

## 5. Fachwortschatz

**Wörter des Kurses, zu verwenden**: Grundgesamtheit, Merkmalsträger, Stichprobe, Merkmal, qualitativ, quantitativ diskret, quantitativ stetig, Klasse, Klassenbreite, absolute Häufigkeit, relative Häufigkeit, kumulierte Häufigkeit, Modalwert, Modalklasse, arithmetisches Mittel, Median, Quartil, Kreisdiagramm, Säulendiagramm, Histogramm, Häufigkeitspolygon, Summenhäufigkeitspolygon, Boxplot.

**Nicht einzuführende Wörter**: Nichts im Material.

## 6. Typische Aufgaben

### 6.1 Diskretes Merkmal

#### 6.1.1

**Das Alter der 20 Mitglieder eines Schachvereins: 14: 3 ; 15: 5 ; 16: 6 ; 17: 4 ; 18: 2. a) Zeichne das Säulendiagramm. b) Gib den Modalwert an. c) Berechne das arithmetische Mittel. d) Bestimme den Median.**
**Verfahren:** Säulendiagramm; $\bar{x}$ mit der Formel; $M$ ist der Mittelwert der Werte an den Stellen 10 und 11.
**Antwort:** b) 16 ; c) $\bar{x} = 317 / 20 = 15{,}85$ ; d) $M = 16$.

#### 6.1.2

**Bestimme für das Alter aus 6.1.1 $Q_1$ und $Q_3$ und zeichne den Boxplot.**
**Verfahren:** kumulierte Häufigkeiten; 25 % von 20 ist 5, also der 5. Wert; 75 % von 20 ist 15, also der 15. Wert.
**Antwort:** $Q_1 = 15$ ; $Q_3 = 17$.

### 6.2 Stetiges Merkmal

#### 6.2.1

**Wartezeit von 40 Patientinnen und Patienten in einer Klinik: $[0 ; 5[$: 4 ; $[5 ; 10[$: 8 ; $[10 ; 20[$: 16 ; $[20 ; 40[$: 12. a) Zeichne das Histogramm mit einer Bezugsbreite von 5 Minuten. b) Welche Klasse hat die größte absolute Häufigkeit?**
**Verfahren:** Höhe = absolute Häufigkeit · 5 / Klassenbreite.
**Antwort:** a) Höhen 4 ; 8 ; 8 ; 3 ; b) $[10 ; 20[$.

#### 6.2.2

**Berechne für die Wartezeiten aus 6.2.1 die kumulierten relativen Häufigkeiten und zeichne ihr Polygon.**
**Verfahren:** die absoluten Häufigkeiten aufsummieren, durch 40 teilen.
**Antwort:** 10 % ; 30 % ; 70 % ; 100 %.

### 6.3 Qualitatives Merkmal

#### 6.3.1

**48 Schülerinnen und Schüler haben ihr Mittagessen gewählt: Nudeln 20, Salat 12, belegtes Brötchen 16. Berechne den Winkel jedes Kreisausschnitts im Kreisdiagramm.**
**Verfahren:** Winkel = absolute Häufigkeit / 48 · 360°.
**Antwort:** 150° ; 90° ; 120°.

## 7. Zu prüfende Punkte

Keine.
