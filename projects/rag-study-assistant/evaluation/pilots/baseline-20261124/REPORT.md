# Engineering Manual Q&A evaluation

Run: 2026-11-24T19:11:36.564437+00:00

20 answerable + 5 unanswerable questions, run independently for each setting. Top-k = 5.

| Chunking | Hit@1 | Hit@5 | Quotation support | Expected-answer check | Missing-answer refusal |
| --- | ---: | ---: | ---: | ---: | ---: |
| 900 chars / 150 overlap | 65% | 90% | 100% | 65% | 100% |
| 450 chars / 75 overlap | 17% | 100% | 100% | 33% | 0% |

## Metric meaning

Hit@k requires a declared relevant page AND evidence anchor in a retrieved chunk. Denominator: 20 answerable questions.
Quotation support checks that the displayed factual answer is assembled only from quotations in the retrieved text. Denominator: non-refused answers; it does not prove answer relevance, source truth, or semantic correctness.
Expected-answer check requires declared text patterns and an expected citation page. This is a narrow deterministic reference check, not a semantic accuracy estimate.
Refusal success is measured separately over the five questions whose answers are missing, including a numeric placeholder.
The initial test set is AI-assisted and small. These are development-set results, not an independently held-out generalization benchmark.

## Failures and raw cases

### 900 chars / 150 overlap

Failure IDs: A02, A03, A11, A12, A13, A15, A19

- A01 PASS: Which main microcontroller is the Arduino UNO R3 equipped with?
  Retrieved pages: [7, 2, 4, 1, 4]; reason: verified_quotations
- A02 FAIL: How many digital input/output pins does the UNO R3 have?
  Retrieved pages: [10, 4, 9, 10, 2]; reason: quote_not_in_source
- A03 FAIL: How many analog inputs are listed for the UNO R3 board?
  Retrieved pages: [4, 4, 10, 2, 6]; reason: quote_not_in_source
- A04 PASS: How much Flash memory is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 5, 4]; reason: verified_quotations
- A05 PASS: How much SRAM is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 5, 4]; reason: verified_quotations
- A06 PASS: How much EEPROM is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 5, 12]; reason: verified_quotations
- A07 PASS: How many 8-bit Timer/Counter peripherals are listed for the ATmega328P?
  Retrieved pages: [2, 7, 10, 4, 1]; reason: verified_quotations
- A08 PASS: How many 16-bit Timer/Counter peripherals are listed for the ATmega328P?
  Retrieved pages: [2, 7, 10, 4, 1]; reason: verified_quotations
- A09 PASS: How many PWM channels are listed for the ATmega328P?
  Retrieved pages: [2, 7, 12, 5, 4]; reason: verified_quotations
- A10 PASS: Which USB bridge processor is identified as component U3 in the board topology table?
  Retrieved pages: [6, 7, 3, 4, 5]; reason: verified_quotations
- A11 FAIL: How much ISP Flash is listed for the ATMega16U2 processor?
  Retrieved pages: [7, 2, 1, 5, 4]; reason: quote_not_in_source
- A12 FAIL: How much EEPROM is listed for the ATMega16U2 processor?
  Retrieved pages: [2, 7, 1, 12, 5]; reason: source_placeholder
- A13 FAIL: What type of USB cable does the manual say is needed to connect the UNO R3 to a computer?
  Retrieved pages: [4, 9, 7, 6, 1]; reason: not_found
- A14 PASS: What software should be installed to program the UNO R3 while offline?
  Retrieved pages: [8, 4, 8, 4, 1]; reason: verified_quotations
- A15 FAIL: Does the USB-B computer connection also provide power to the UNO R3?
  Retrieved pages: [7, 5, 4, 4, 6]; reason: not_found
- A16 PASS: Where can sample sketches for the UNO R3 be found in the Arduino IDE?
  Retrieved pages: [8, 8, 4, 11, 4]; reason: verified_quotations
- A17 PASS: What voltage is the IOREF digital logic reference connected to in the JANALOG table?
  Retrieved pages: [10, 10, 6, 14, 5]; reason: verified_quotations
- A18 PASS: What I2C function is assigned to pin A4/SDA in the JANALOG connector table?
  Retrieved pages: [10, 10, 9, 6, 3]; reason: verified_quotations
- A19 FAIL: What I2C function is assigned to pin A5/SCL in the JANALOG connector table?
  Retrieved pages: [10, 9, 10, 6, 3]; reason: quote_not_in_source
- A20 PASS: What DC barrel jack voltage range is listed in the power consumption table?
  Retrieved pages: [5, 6, 7, 14, 3]; reason: verified_quotations
- U01 PASS: How much does the UNO R3 board weigh in grams?
  Retrieved pages: [4, 11, 4, 5, 6]; reason: not_found
- U02 PASS: What is the UNO R3 current retail price in US dollars?
  Retrieved pages: [4, 4, 11, 10, 7]; reason: not_found
- U03 PASS: What Bluetooth version is built into the UNO R3?
  Retrieved pages: [2, 4, 4, 1, 7]; reason: not_found
- U04 PASS: What is the capacity in mAh of a battery included with the UNO R3?
  Retrieved pages: [5, 4, 2, 4, 7]; reason: not_found
- U05 PASS: What is the numeric maximum power consumption PMax in milliamps?
  Retrieved pages: [5, 7, 12, 13, 13]; reason: not_found
### 450 chars / 75 overlap

Failure IDs: A02, A03, A05, A06

- A01 PASS: Which main microcontroller is the Arduino UNO R3 equipped with?
  Retrieved pages: [2, 2, 7, 4, 1]; reason: verified_quotations
- A02 FAIL: How many digital input/output pins does the UNO R3 have?
  Retrieved pages: [10, 10, 4, 10, 10]; reason: verified_quotations
- A03 FAIL: How many analog inputs are listed for the UNO R3 board?
  Retrieved pages: [4, 10, 4, 2, 4]; reason: quote_not_in_source
- A04 PASS: How much Flash memory is listed for the ATmega328P processor?
  Retrieved pages: [2, 7, 2, 2, 4]; reason: verified_quotations
- A05 FAIL: How much SRAM is listed for the ATmega328P processor?
  Retrieved pages: [2, 2, 7, 2, 1]; reason: verified_quotations
- A06 FAIL: How much EEPROM is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 2, 4, 2]; reason: verified_quotations

## Source limitations

The source contains conflicting 16 MHz/20 MHz processor statements and an xx mA power-consumption placeholder. Do not treat quotations as engineering approval. Diagrams are not OCR'd or interpreted.
See results.json for all retrieved chunks, model outputs, exact source hashes, timing, settings, and per-case scores.
