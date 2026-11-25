# Engineering Manual Q&A evaluation

Run: 2026-11-24T19:30:35.871409+00:00

20 answerable + 5 unanswerable questions, run independently for each setting. Top-k = 5.

| Chunking | Hit@1 | Hit@5 | Quotation support | Expected-answer check | Missing-answer refusal |
| --- | ---: | ---: | ---: | ---: | ---: |
| 900 chars / 150 overlap | 65% | 95% | 100% | 90% | 100% |
| 450 chars / 75 overlap | 50% | 100% | 100% | 70% | 100% |

## Metric meaning

Hit@k requires a declared relevant page AND evidence anchor in a retrieved chunk. Denominator: 20 answerable questions.
Quotation support checks that the displayed factual answer is assembled only from quotations in the retrieved text. Denominator: non-refused answers; it does not prove answer relevance, source truth, or semantic correctness.
Expected-answer check requires declared text patterns and an expected citation page. This is a narrow deterministic reference check, not a semantic accuracy estimate.
Refusal success is measured separately over the five questions whose answers are missing, including a numeric placeholder.
The initial test set is AI-assisted and small. These are development-set results, not an independently held-out generalization benchmark.

## Failures and raw cases

### 900 chars / 150 overlap

Failure IDs: A15, A18

- A01 PASS: Which main microcontroller is the Arduino UNO R3 equipped with?
  Retrieved pages: [2, 4, 7, 1, 6]; reason: verified_quotations
- A02 PASS: How many digital input/output pins does the UNO R3 have?
  Retrieved pages: [4, 10, 2, 6, 9]; reason: verified_quotations
- A03 PASS: How many analog inputs are listed for the UNO R3 board?
  Retrieved pages: [4, 2, 6, 10, 4]; reason: verified_quotations
- A04 PASS: How much Flash memory is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 4, 5]; reason: verified_quotations
- A05 PASS: How much SRAM is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 4, 6]; reason: verified_quotations
- A06 PASS: How much EEPROM is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 12, 4]; reason: verified_quotations
- A07 PASS: How many 8-bit Timer/Counter peripherals are listed for the ATmega328P?
  Retrieved pages: [2, 7, 1, 4, 10]; reason: verified_quotations
- A08 PASS: How many 16-bit Timer/Counter peripherals are listed for the ATmega328P?
  Retrieved pages: [2, 7, 1, 4, 10]; reason: verified_quotations
- A09 PASS: How many PWM channels are listed for the ATmega328P?
  Retrieved pages: [2, 7, 1, 6, 12]; reason: verified_quotations
- A10 PASS: Which USB bridge processor is identified as component U3 in the board topology table?
  Retrieved pages: [6, 7, 1, 5, 4]; reason: verified_quotations
- A11 PASS: How much ISP Flash is listed for the ATMega16U2 processor?
  Retrieved pages: [7, 2, 1, 4, 13]; reason: verified_quotations
- A12 PASS: How much EEPROM is listed for the ATMega16U2 processor?
  Retrieved pages: [2, 7, 1, 4, 12]; reason: verified_quotations
- A13 PASS: What type of USB cable does the manual say is needed to connect the UNO R3 to a computer?
  Retrieved pages: [6, 4, 8, 7, 1]; reason: verified_quotations
- A14 PASS: What software should be installed to program the UNO R3 while offline?
  Retrieved pages: [8, 4, 8, 1, 2]; reason: verified_quotations
- A15 FAIL: Does the USB-B computer connection also provide power to the UNO R3?
  Retrieved pages: [7, 5, 4, 6, 2]; reason: verified_quotations
- A16 PASS: Where can sample sketches for the UNO R3 be found in the Arduino IDE?
  Retrieved pages: [8, 8, 4, 1, 2]; reason: verified_quotations
- A17 PASS: What voltage is the IOREF digital logic reference connected to in the JANALOG table?
  Retrieved pages: [10, 10, 5, 6, 14]; reason: verified_quotations
- A18 FAIL: What I2C function is assigned to pin A4/SDA in the JANALOG connector table?
  Retrieved pages: [10, 10, 6, 9, 1]; reason: invalid_evidence_list
- A19 PASS: What I2C function is assigned to pin A5/SCL in the JANALOG connector table?
  Retrieved pages: [10, 10, 6, 9, 13]; reason: verified_quotations
- A20 PASS: What DC barrel jack voltage range is listed in the power consumption table?
  Retrieved pages: [5, 6, 12, 7, 10]; reason: verified_quotations
- U01 PASS: How much does the UNO R3 board weigh in grams?
  Retrieved pages: [4, 1, 5, 4, 6]; reason: not_found
- U02 PASS: What is the UNO R3 current retail price in US dollars?
  Retrieved pages: [4, 2, 1, 4, 5]; reason: not_found
- U03 PASS: What Bluetooth version is built into the UNO R3?
  Retrieved pages: [2, 4, 7, 1, 6]; reason: not_found
- U04 PASS: What is the capacity in mAh of a battery included with the UNO R3?
  Retrieved pages: [5, 2, 4, 7, 1]; reason: not_found
- U05 PASS: What is the numeric maximum power consumption PMax in milliamps?
  Retrieved pages: [5, 12, 7, 13, 13]; reason: not_found
### 450 chars / 75 overlap

Failure IDs: A01, A04, A05, A12, A16, A17

- A01 FAIL: Which main microcontroller is the Arduino UNO R3 equipped with?
  Retrieved pages: [2, 2, 2, 4, 1]; reason: verified_quotations
- A02 PASS: How many digital input/output pins does the UNO R3 have?
  Retrieved pages: [4, 10, 2, 2, 2]; reason: verified_quotations
- A03 PASS: How many analog inputs are listed for the UNO R3 board?
  Retrieved pages: [4, 2, 10, 2, 6]; reason: verified_quotations
- A04 FAIL: How much Flash memory is listed for the ATmega328P processor?
  Retrieved pages: [2, 2, 7, 4, 2]; reason: invalid_evidence_list
- A05 FAIL: How much SRAM is listed for the ATmega328P processor?
  Retrieved pages: [2, 2, 7, 4, 1]; reason: invalid_evidence_list
- A06 PASS: How much EEPROM is listed for the ATmega328P processor?
  Retrieved pages: [2, 7, 2, 4, 1]; reason: verified_quotations
- A07 PASS: How many 8-bit Timer/Counter peripherals are listed for the ATmega328P?
  Retrieved pages: [2, 2, 4, 2, 7]; reason: verified_quotations
- A08 PASS: How many 16-bit Timer/Counter peripherals are listed for the ATmega328P?
  Retrieved pages: [2, 2, 4, 2, 7]; reason: verified_quotations
- A09 PASS: How many PWM channels are listed for the ATmega328P?
  Retrieved pages: [7, 2, 2, 2, 4]; reason: verified_quotations
- A10 PASS: Which USB bridge processor is identified as component U3 in the board topology table?
  Retrieved pages: [6, 7, 5, 4, 1]; reason: verified_quotations
- A11 PASS: How much ISP Flash is listed for the ATMega16U2 processor?
  Retrieved pages: [2, 7, 2, 2, 1]; reason: verified_quotations
- A12 FAIL: How much EEPROM is listed for the ATMega16U2 processor?
  Retrieved pages: [2, 2, 7, 2, 1]; reason: invalid_evidence_list
- A13 PASS: What type of USB cable does the manual say is needed to connect the UNO R3 to a computer?
  Retrieved pages: [4, 8, 6, 2, 5]; reason: verified_quotations
- A14 PASS: What software should be installed to program the UNO R3 while offline?
  Retrieved pages: [8, 8, 4, 4, 8]; reason: verified_quotations
- A15 PASS: Does the USB-B computer connection also provide power to the UNO R3?
  Retrieved pages: [5, 4, 7, 8, 5]; reason: verified_quotations
- A16 FAIL: Where can sample sketches for the UNO R3 be found in the Arduino IDE?
  Retrieved pages: [8, 8, 8, 8, 4]; reason: invalid_evidence_list
- A17 FAIL: What voltage is the IOREF digital logic reference connected to in the JANALOG table?
  Retrieved pages: [10, 10, 10, 10, 5]; reason: invalid_evidence_list
- A18 PASS: What I2C function is assigned to pin A4/SDA in the JANALOG connector table?
  Retrieved pages: [10, 10, 10, 10, 6]; reason: verified_quotations
- A19 PASS: What I2C function is assigned to pin A5/SCL in the JANALOG connector table?
  Retrieved pages: [10, 10, 10, 10, 6]; reason: verified_quotations
- A20 PASS: What DC barrel jack voltage range is listed in the power consumption table?
  Retrieved pages: [5, 5, 10, 6, 12]; reason: verified_quotations
- U01 PASS: How much does the UNO R3 board weigh in grams?
  Retrieved pages: [4, 4, 1, 5, 2]; reason: not_found
- U02 PASS: What is the UNO R3 current retail price in US dollars?
  Retrieved pages: [4, 2, 4, 2, 1]; reason: not_found
- U03 PASS: What Bluetooth version is built into the UNO R3?
  Retrieved pages: [2, 2, 2, 4, 4]; reason: not_found
- U04 PASS: What is the capacity in mAh of a battery included with the UNO R3?
  Retrieved pages: [2, 5, 2, 5, 4]; reason: not_found
- U05 PASS: What is the numeric maximum power consumption PMax in milliamps?
  Retrieved pages: [5, 5, 12, 7, 13]; reason: not_found

## Source limitations

The source contains conflicting 16 MHz/20 MHz processor statements and an xx mA power-consumption placeholder. Do not treat quotations as engineering approval. Diagrams are not OCR'd or interpreted.
See results.json for all retrieved chunks, model outputs, exact source hashes, timing, settings, and per-case scores.
