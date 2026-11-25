# Engineering manual source

The demonstration uses Arduino's **Arduino UNO R3 User Manual**, product A000066, downloaded November 24, 2026 from https://docs.arduino.cc/resources/datasheets/A000066-datasheet.pdf . The PDF contains 14 pages and is marked modified November 19, 2026. The precise source hash and revision information are in sources.json.

Publisher: Arduino S.r.l. Arduino names, logos, and product marks belong to their owners. No endorsement is implied.

Arduino states that its website's editorial text and photos are released under CC BY-SA 4.0: https://www.arduino.cc/en/trademark . Its documentation contribution policy also identifies CC BY-SA 4.0: https://github.com/arduino/docs-content/blob/main/CONTRIBUTING.md . This educational application attributes its source; the PDF is obtained unmodified from the publisher and is not committed to the repository. Do not assume third-party artwork or marks are separately licensed. Source quotations and adaptations of Arduino editorial content retain attribution and the applicable CC BY-SA conditions; the application does not grant rights to third-party material.

Run scripts/download_manual.py to obtain the exact fixture. If the publisher changes the file, the hash check stops; update the manifest and reference set only after reviewing the new PDF. Do not silently change source content to make a test pass.

The evaluation questions are AI-assisted and reference the original PDF page numbers, not printed chapter numbers. Short evidence anchors identify relevant passages. They were checked against the extracted text and visually reviewed on the relevant pages. Ali must review the set and add his own cases as part of project defense.

Do not add private PDFs or other personal material to Git. Generated indexes stay in memory. Arbitrary user-selected PDFs get a hash-based source ID and are explicitly marked as having unverified publisher/usage metadata.

Known source issues: page 2 says up to 16 MHz while page 7 says up to 20 MHz; page 5 gives PMax as xx mA. The program must not turn these into a single invented engineering specification.
