"""
Seed database with Mills v. Polley case data
26 weapons, 5 strategies, 4 perjury paths, 12 COAs, 9 source documents
"""
from database import AsyncSessionLocal
from models import Case, Document, COA, BurdenElement, Weapon, Strategy, PerjuryPath
from datetime import datetime


async def seed_initial_data():
    """Seed database with Mills v. Polley case"""
    async with AsyncSessionLocal() as db:
        # Check if data already seeded
        existing_case = await db.execute("SELECT COUNT(*) FROM cases")
        if existing_case is not None and existing_case > 0:
            return

        # Create main case
        case = Case(
            name="Mills v. Polley",
            court="Sacramento County Superior Court",
            plaintiff="Jeremy Mills",
            defendant="David Polley",
            status="active",
            created_at=datetime.utcnow()
        )
        db.add(case)
        await db.flush()
        case_id = case.id

        # Add documents (9 source files)
        documents = [
            {
                "filename": "Email_2023_03_15.eml",
                "folder": "emails",
                "file_type": "email",
                "text_content": "David's email acknowledging the breach of contract terms and failure to remit funds as promised.",
                "char_count": 245,
                "sha256_hash": "abc123def456"
            },
            {
                "filename": "Bank_Records_Feb_2023.pdf",
                "folder": "financial",
                "file_type": "pdf",
                "text_content": "Bank statement showing $0 balance on Feb 1, 2023 and $285K deposit on Feb 2, 2023 without explanation.",
                "char_count": 512,
                "sha256_hash": "def789ghi012"
            },
            {
                "filename": "Contract_Amendment_2022.docx",
                "folder": "contracts",
                "file_type": "text",
                "text_content": "Signed contract amendment clearly stating payment terms and obligations regarding profit distribution.",
                "char_count": 1200,
                "sha256_hash": "ghi345jkl678"
            },
            {
                "filename": "Entity_Formation_Docs.pdf",
                "folder": "corporate",
                "file_type": "pdf",
                "text_content": "Corporate entity formation documents showing David's direct involvement in shell company creation.",
                "char_count": 890,
                "sha256_hash": "jkl901mno234"
            },
            {
                "filename": "Witness_Statement_Alice_Chen.docx",
                "folder": "witness",
                "file_type": "text",
                "text_content": "Witness statement from Alice Chen confirming David's false statements during March 15 meeting.",
                "char_count": 450,
                "sha256_hash": "mno567pqr890"
            },
            {
                "filename": "Email_Thread_June_2023.eml",
                "folder": "emails",
                "file_type": "email",
                "text_content": "Email thread showing timeline contradiction: David claims June 18 notification but bank records show June 14 activity.",
                "char_count": 680,
                "sha256_hash": "pqr123stu456"
            },
            {
                "filename": "Financial_Analysis_Q1_2023.xlsx",
                "folder": "financial",
                "file_type": "pdf",
                "text_content": "Q1 2023 financial analysis showing impossible fund sources and unauthorized transfers.",
                "char_count": 1100,
                "sha256_hash": "stu789vwx012"
            },
            {
                "filename": "Deposition_Transcript_Polley.txt",
                "folder": "discovery",
                "file_type": "text",
                "text_content": "Full deposition transcript of David Polley containing multiple inconsistencies and admissions.",
                "char_count": 2500,
                "sha256_hash": "vwx345yza678"
            },
            {
                "filename": "Corporate_Structure_Diagram.pdf",
                "folder": "corporate",
                "file_type": "pdf",
                "text_content": "Organizational diagram showing how shell entities were used to conceal asset transfers.",
                "char_count": 420,
                "sha256_hash": "yza901bcd234"
            }
        ]

        for doc_data in documents:
            doc = Document(
                case_id=case_id,
                **doc_data,
                created_at=datetime.utcnow()
            )
            db.add(doc)

        # Add COAs (12 Causes of Action)
        coas_data = [
            {"name": "Breach of Contract", "caci_ref": "CACI 303", "strength": 92.0, "evidence_count": 8},
            {"name": "Fraud", "caci_ref": "CACI 1900", "strength": 85.0, "evidence_count": 7},
            {"name": "Fraudulent Inducement", "caci_ref": "CACI 1902", "strength": 78.0, "evidence_count": 6},
            {"name": "Negligent Misrepresentation", "caci_ref": "CACI 1906", "strength": 72.0, "evidence_count": 5},
            {"name": "Fiduciary Duty Breach", "caci_ref": "CACI 4101", "strength": 88.0, "evidence_count": 7},
            {"name": "Conversion", "caci_ref": "CACI 2100", "strength": 80.0, "evidence_count": 6},
            {"name": "Unjust Enrichment", "caci_ref": "CACI 3050", "strength": 75.0, "evidence_count": 5},
            {"name": "Money Had and Received", "caci_ref": "CACI 3051", "strength": 70.0, "evidence_count": 4},
            {"name": "Quantum Meruit", "caci_ref": "CACI 3052", "strength": 68.0, "evidence_count": 4},
            {"name": "Constructive Fraud", "caci_ref": "CACI 1903", "strength": 82.0, "evidence_count": 6},
            {"name": "Breach of Implied Covenant", "caci_ref": "CACI 305", "strength": 76.0, "evidence_count": 5},
            {"name": "Corporate Waste", "caci_ref": "CACI 4102", "strength": 65.0, "evidence_count": 4}
        ]

        coa_map = {}
        for coa_data in coas_data:
            coa = COA(
                case_id=case_id,
                **coa_data,
                status="pending",
                coverage_pct=0.0,
                created_at=datetime.utcnow()
            )
            db.add(coa)
            await db.flush()
            coa_map[coa_data["name"]] = coa.id

            # Add burden elements for each COA
            if coa_data["name"] == "Breach of Contract":
                elements = [
                    {"element_id": "B1", "description": "Contract existed"},
                    {"element_id": "B2", "description": "Plaintiff performed or excused"},
                    {"element_id": "B3", "description": "Defendant breached"}
                ]
            elif coa_data["name"] == "Fraud":
                elements = [
                    {"element_id": "F1", "description": "Misrepresentation"},
                    {"element_id": "F2", "description": "Knowledge of falsity"},
                    {"element_id": "F3", "description": "Intent to induce"},
                    {"element_id": "F4", "description": "Reliance"},
                    {"element_id": "F5", "description": "Damages"}
                ]
            elif coa_data["name"] == "Fiduciary Duty Breach":
                elements = [
                    {"element_id": "FD1", "description": "Fiduciary relationship"},
                    {"element_id": "FD2", "description": "Breach of duty"},
                    {"element_id": "FD3", "description": "Causation"},
                    {"element_id": "FD4", "description": "Damages"}
                ]
            else:
                elements = [
                    {"element_id": "E1", "description": "Essential element one"},
                    {"element_id": "E2", "description": "Essential element two"}
                ]

            for elem_data in elements:
                element = BurdenElement(
                    coa_id=coa.id,
                    **elem_data,
                    strength=0.7,
                    supporting_docs={"docs": []}
                )
                db.add(element)

        # Add 26 Weapons
        weapons_data = [
            {"id": 1, "category": "UNCOVER", "coa": "Breach of Contract", "caci": "CACI 303", "strategy": "Document Pincer", "question": "Isn't this the exact contract you signed?", "evidence_score": 92.0, "perjury_trap": False},
            {"id": 2, "category": "DISCOVER", "coa": "Fraud", "caci": "CACI 1900", "strategy": "Admissions Cascade", "question": "Did you or did you not receive the email?", "evidence_score": 78.0, "perjury_trap": True},
            {"id": 3, "category": "WEAPONIZE", "coa": "Fraud", "caci": "CACI 1900", "strategy": "Double Bind", "question": "Either you knew or you didn't - which is it?", "evidence_score": 70.0, "perjury_trap": True},
            {"id": 4, "category": "UNCOVER", "coa": "Fraud", "caci": "CACI 1900", "strategy": "Financial Trap", "question": "Where did the $285K come from?", "evidence_score": 88.0, "perjury_trap": True},
            {"id": 5, "category": "DISCOVER", "coa": "Fraudulent Inducement", "caci": "CACI 1902", "strategy": "Timeline Trap", "question": "When exactly did you learn of this?", "evidence_score": 75.0, "perjury_trap": False},
            {"id": 6, "category": "WEAPONIZE", "coa": "Fraudulent Inducement", "caci": "CACI 1902", "strategy": "Witness Contradiction", "question": "Isn't that exactly opposite of what Alice testified?", "evidence_score": 82.0, "perjury_trap": True},
            {"id": 7, "category": "UNCOVER", "coa": "Negligent Misrepresentation", "caci": "CACI 1906", "strategy": "Document Pincer", "question": "What does your own email say here?", "evidence_score": 79.0, "perjury_trap": False},
            {"id": 8, "category": "WEAPONIZE", "coa": "Fraud", "caci": "CACI 1900", "strategy": "Admissions Cascade", "question": "So you admit you signed this?", "evidence_score": 78.0, "perjury_trap": False},
            {"id": 9, "category": "WEAPONIZE", "coa": "Fraud", "caci": "CACI 1900", "strategy": "Double Bind", "question": "Which version of events is true?", "evidence_score": 70.0, "perjury_trap": True},
            {"id": 10, "category": "DISCOVER", "coa": "Fiduciary Duty Breach", "caci": "CACI 4101", "strategy": "Entity Shell Game", "question": "Why create this entity without telling Jeremy?", "evidence_score": 82.0, "perjury_trap": False},
            {"id": 11, "category": "UNCOVER", "coa": "Fiduciary Duty Breach", "caci": "CACI 4101", "strategy": "Corporate Governance Void", "question": "What board approval did you get?", "evidence_score": 70.0, "perjury_trap": True},
            {"id": 12, "category": "WEAPONIZE", "coa": "Conversion", "caci": "CACI 2100", "strategy": "Financial Trap", "question": "Those funds belonged to whom?", "evidence_score": 85.0, "perjury_trap": True},
            {"id": 13, "category": "DISCOVER", "coa": "Unjust Enrichment", "caci": "CACI 3050", "strategy": "Quantum Meruit", "question": "How much did you personally benefit?", "evidence_score": 72.0, "perjury_trap": False},
            {"id": 14, "category": "WEAPONIZE", "coa": "Fiduciary Duty Breach", "caci": "CACI 4101", "strategy": "Entity Shell Game", "question": "Isn't the real purpose to hide assets?", "evidence_score": 82.0, "perjury_trap": True},
            {"id": 15, "category": "UNCOVER", "coa": "Breach of Contract", "caci": "CACI 303", "strategy": "Document Pincer", "question": "Can you read paragraph 3 aloud?", "evidence_score": 90.0, "perjury_trap": False},
            {"id": 16, "category": "DISCOVER", "coa": "Fraudulent Inducement", "caci": "CACI 1902", "strategy": "Timeline Trap", "question": "So this happened before or after June 14?", "evidence_score": 68.0, "perjury_trap": False},
            {"id": 17, "category": "WEAPONIZE", "coa": "Constructive Fraud", "caci": "CACI 1903", "strategy": "Concealment Chain", "question": "Why didn't you disclose this structure?", "evidence_score": 80.0, "perjury_trap": True},
            {"id": 18, "category": "UNCOVER", "coa": "Money Had and Received", "caci": "CACI 3051", "strategy": "Financial Impossibility", "question": "Account showed zero on March 15 - true?", "evidence_score": 75.0, "perjury_trap": False},
            {"id": 19, "category": "DISCOVER", "coa": "Breach of Implied Covenant", "caci": "CACI 305", "strategy": "Good Faith Destruction", "question": "Did you act in good faith?", "evidence_score": 72.0, "perjury_trap": False},
            {"id": 20, "category": "WEAPONIZE", "coa": "Conversion", "caci": "CACI 2100", "strategy": "Document Pincer", "question": "These were joint account funds?", "evidence_score": 88.0, "perjury_trap": True},
            {"id": 21, "category": "UNCOVER", "coa": "Corporate Waste", "caci": "CACI 4102", "strategy": "Entity Shell Game", "question": "What was the business purpose?", "evidence_score": 65.0, "perjury_trap": False},
            {"id": 22, "category": "DISCOVER", "coa": "Fraud", "caci": "CACI 1900", "strategy": "Pattern Recognition", "question": "Isn't this part of a pattern?", "evidence_score": 76.0, "perjury_trap": False},
            {"id": 23, "category": "WEAPONIZE", "coa": "Fraudulent Inducement", "caci": "CACI 1902", "strategy": "Timeline Trap", "question": "Your story requires what to be true?", "evidence_score": 65.0, "perjury_trap": True},
            {"id": 24, "category": "UNCOVER", "coa": "Breach of Contract", "caci": "CACI 303", "strategy": "Timeline Trap", "question": "What order did these events happen in?", "evidence_score": 65.0, "perjury_trap": False},
            {"id": 25, "category": "DISCOVER", "coa": "Fiduciary Duty Breach", "caci": "CACI 4101", "strategy": "Disclosure Trap", "question": "Did you ever tell Jeremy about this?", "evidence_score": 74.0, "perjury_trap": False},
            {"id": 26, "category": "WEAPONIZE", "coa": "Fiduciary Duty Breach", "caci": "CACI 4101", "strategy": "Corporate Governance Void", "question": "Where's the board authorization?", "evidence_score": 70.0, "perjury_trap": True}
        ]

        for weapon_data in weapons_data:
            weapon = Weapon(
                case_id=case_id,
                category=weapon_data["category"],
                coa_ref=weapon_data["coa"],
                caci=weapon_data["caci"],
                element="element",
                strategy=weapon_data["strategy"],
                strategy_type=weapon_data["category"],
                question=weapon_data["question"],
                strengthens_jeremy="Strong support for plaintiff claim",
                weakens_david="Undermines defendant position",
                perjury_push="Creates testimony contradiction",
                evidence_score=weapon_data["evidence_score"],
                perjury_trap=weapon_data["perjury_trap"],
                docs_json={"docs": [1, 2, 3]},
                opp_prediction="Defense will contest document authenticity",
                depo_strategy="Lock in testimony then confront with document",
                long_game="Establish pattern of deception across multiple COAs",
                responses_json={"responses": []},
                attorney_notes="",
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(weapon)

        # Add 5 Strategies
        strategies_data = [
            {
                "name": "Admissions Cascade",
                "emoji": "📋",
                "weapons_json": {"weapon_ids": [2, 8]},
                "rationale": "Lock David into admissions early, then challenge each step",
                "value_score": 85.0,
                "depo_impact": 90.0,
                "trial_impact": 80.0,
                "phases_json": {"phase1": "discovery", "phase2": "deposition", "phase3": "trial"}
            },
            {
                "name": "Document Pincer",
                "emoji": "📌",
                "weapons_json": {"weapon_ids": [1, 7, 15, 20]},
                "rationale": "Use documents to create inescapable logical trap",
                "value_score": 92.0,
                "depo_impact": 95.0,
                "trial_impact": 88.0,
                "phases_json": {"phase1": "discovery", "phase2": "deposition", "phase3": "trial"}
            },
            {
                "name": "Timeline Trap",
                "emoji": "⏰",
                "weapons_json": {"weapon_ids": [5, 16, 24]},
                "rationale": "Establish impossible timeline through dated documents",
                "value_score": 78.0,
                "depo_impact": 82.0,
                "trial_impact": 75.0,
                "phases_json": {"phase1": "discovery", "phase2": "deposition", "phase3": "trial"}
            },
            {
                "name": "Entity Shell Game",
                "emoji": "🎭",
                "weapons_json": {"weapon_ids": [10, 14, 21]},
                "rationale": "Expose hidden corporate structure and asset concealment",
                "value_score": 82.0,
                "depo_impact": 88.0,
                "trial_impact": 85.0,
                "phases_json": {"phase1": "discovery", "phase2": "deposition", "phase3": "trial"}
            },
            {
                "name": "Financial Impossibility",
                "emoji": "💰",
                "weapons_json": {"weapon_ids": [4, 12, 18]},
                "rationale": "Show funds couldn't have come from David's account",
                "value_score": 88.0,
                "depo_impact": 92.0,
                "trial_impact": 86.0,
                "phases_json": {"phase1": "discovery", "phase2": "deposition", "phase3": "trial"}
            }
        ]

        for strategy_data in strategies_data:
            strategy = Strategy(
                case_id=case_id,
                **strategy_data,
                created_at=datetime.utcnow()
            )
            db.add(strategy)

        # Add 4 Perjury Paths
        perjury_paths_data = [
            {
                "name": "Financial Trap",
                "desc": "David's account could not have generated funds he claims to have transferred",
                "weapons_json": {"weapon_ids": [4, 12, 18]},
                "logic": "If David truly had $285K, where did it come from? His account was zero.",
                "trap_springs": "He either admits misappropriation or claims unknown source (creates new liability)"
            },
            {
                "name": "Entity Shell Game",
                "desc": "Hidden corporate entities were created to conceal asset transfers from Jeremy",
                "weapons_json": {"weapon_ids": [10, 14, 21]},
                "logic": "Why would legitimate entities be created secretly without Jeremy's knowledge?",
                "trap_springs": "Admission of concealment proves fiduciary breach; denial contradicts documents"
            },
            {
                "name": "Concealment Chain",
                "desc": "Series of undisclosed transactions designed to hide true asset flow",
                "weapons_json": {"weapon_ids": [17, 25]},
                "logic": "Each omission was intentional; pattern shows premeditation",
                "trap_springs": "Defense must prove each non-disclosure was accidental (mathematically impossible)"
            },
            {
                "name": "Timeline Destroy",
                "desc": "David's account of event sequence is physically impossible given dated evidence",
                "weapons_json": {"weapon_ids": [5, 16, 24]},
                "logic": "Bank record dated June 14 proves David knew before he claims (June 18)",
                "trap_springs": "No plausible explanation for timeline conflict other than perjury"
            }
        ]

        for path_data in perjury_paths_data:
            path = PerjuryPath(
                case_id=case_id,
                **path_data,
                created_at=datetime.utcnow()
            )
            db.add(path)

        # Commit all data
        await db.commit()
        print(f"Seeded case {case_id}: Mills v. Polley with all data")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_initial_data())
