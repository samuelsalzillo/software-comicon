"""
Test per verificare che il problema del mescolamento code sia risolto.
"""
import os
import sys
import tempfile
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.GameBackend import GameBackend


def setup_test_db():
    """Setup test database."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.environ['SQLITE_DB_PATH'] = db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mid_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            couple_type TEXT,
            mid_duration_minutes REAL
        )
    """)

    conn.commit()
    conn.close()

    return db_path


def cleanup_test_db(db_path):
    """Cleanup test database."""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except:
        pass


def test_scenario_1():
    """
    Test Scenario 1: Coppia in gioco, Singolo deve entrare quando Alfa si libera

    Setup:
    - Coda Coppie: [GIALLO-002]
    - Coda Singoli: [BLU-001]
    - Start GIALLO-001 (coppia) → Occupa Alfa e Bravo
    - Premi terzo pulsante → Libera Alfa (Bravo ancora occupata)

    Risultato Atteso:
    - Next player deve essere BLU-001 (singolo) NON GIALLO-002 (coppia)
    """
    print("\n" + "="*70)
    print("TEST SCENARIO 1: Singolo deve entrare durante coppia")
    print("="*70)

    db_path = setup_test_db()

    try:
        backend = GameBackend()

        # Setup
        print("\n1. Setup code:")
        backend.add_couple('GIALLO-001', 'Coppia 1')
        backend.add_couple('GIALLO-002', 'Coppia 2')
        backend.add_single('BLU-001', 'Singolo 1')

        print(f"   - Coda Coppie: {[p['id'] for p in backend.queue_couples]}")
        print(f"   - Coda Singoli: {[p['id'] for p in backend.queue_singles]}")

        # Start coppia
        print("\n2. Start GIALLO-001 (coppia):")
        backend.start_game(is_couple=True)
        print(f"   - Alfa: {backend.current_player_alfa['id'] if backend.current_player_alfa else 'Libera'}")
        print(f"   - Bravo: {backend.current_player_bravo['id'] if backend.current_player_bravo else 'Libera'}")
        print(f"   - Next player: {backend.next_player_alfa_bravo_id}")

        # Press third button
        print("\n3. Premi terzo pulsante (libera Alfa):")
        backend.button_third_pressed()
        print(f"   - Alfa: {backend.current_player_alfa['id'] if backend.current_player_alfa else 'Libera'}")
        print(f"   - Bravo: {backend.current_player_bravo['id'] if backend.current_player_bravo else 'Libera'}")
        print(f"   - Next player: {backend.next_player_alfa_bravo_id}")

        # Verify
        print("\n4. Verifica:")
        if backend.next_player_alfa_bravo_id == 'BLU-001':
            print("   ✅ PASS: Next player è BLU-001 (singolo) - CORRETTO!")
            result = True
        else:
            print(f"   ❌ FAIL: Next player è {backend.next_player_alfa_bravo_id}")
            print(f"            Dovrebbe essere BLU-001")
            result = False

        return result

    finally:
        cleanup_test_db(db_path)


def test_scenario_2():
    """
    Test Scenario 2: Entrambe libere, Coppia ha priorità

    Setup:
    - Coda Coppie: [GIALLO-001]
    - Coda Singoli: [BLU-001]
    - Alfa: Libera
    - Bravo: Libera

    Risultato Atteso:
    - Next player deve essere GIALLO-001 (coppia) NON BLU-001 (singolo)
    """
    print("\n" + "="*70)
    print("TEST SCENARIO 2: Coppie hanno priorità quando entrambe libere")
    print("="*70)

    db_path = setup_test_db()

    try:
        backend = GameBackend()

        # Setup
        print("\n1. Setup code:")
        backend.add_single('BLU-001', 'Singolo 1')  # Aggiungi singolo per primo
        backend.add_couple('GIALLO-001', 'Coppia 1')  # Coppia aggiunta dopo

        print(f"   - Coda Singoli: {[p['id'] for p in backend.queue_singles]}")
        print(f"   - Coda Coppie: {[p['id'] for p in backend.queue_couples]}")

        # Update next player
        print("\n2. Update next player:")
        backend.update_next_player()
        print(f"   - Alfa: {backend.current_player_alfa['id'] if backend.current_player_alfa else 'Libera'}")
        print(f"   - Bravo: {backend.current_player_bravo['id'] if backend.current_player_bravo else 'Libera'}")
        print(f"   - Next player: {backend.next_player_alfa_bravo_id}")

        # Verify
        print("\n3. Verifica:")
        if backend.next_player_alfa_bravo_id == 'GIALLO-001':
            print("   ✅ PASS: Next player è GIALLO-001 (coppia) - CORRETTO!")
            result = True
        else:
            print(f"   ❌ FAIL: Next player è {backend.next_player_alfa_bravo_id}")
            print(f"            Dovrebbe essere GIALLO-001")
            result = False

        return result

    finally:
        cleanup_test_db(db_path)


def test_scenario_3():
    """
    Test Scenario 3: Solo Alfa libera, NESSUN singolo in coda

    Setup:
    - Coda Coppie: [GIALLO-002]
    - Coda Singoli: []
    - Alfa: Libera
    - Bravo: GIALLO-001 (occupata)

    Risultato Atteso:
    - Next player deve essere None (coppia non può entrare)
    - Sistema attende che Bravo si liberi
    """
    print("\n" + "="*70)
    print("TEST SCENARIO 3: Coppia non può entrare con solo Alfa libera")
    print("="*70)

    db_path = setup_test_db()

    try:
        backend = GameBackend()

        # Setup - start coppia e poi press third
        print("\n1. Setup:")
        backend.add_couple('GIALLO-001', 'Coppia 1')
        backend.add_couple('GIALLO-002', 'Coppia 2')

        backend.start_game(is_couple=True)
        backend.button_third_pressed()

        print(f"   - Coda Coppie: {[p['id'] for p in backend.queue_couples]}")
        print(f"   - Coda Singoli: {[p['id'] for p in backend.queue_singles]}")
        print(f"   - Alfa: {backend.current_player_alfa['id'] if backend.current_player_alfa else 'Libera'}")
        print(f"   - Bravo: {backend.current_player_bravo['id'] if backend.current_player_bravo else 'Libera'}")

        # Verify
        print("\n2. Verifica:")
        print(f"   - Next player: {backend.next_player_alfa_bravo_id}")

        if backend.next_player_alfa_bravo_id is None:
            print("   ✅ PASS: Next player è None - CORRETTO!")
            print("            (Coppia non può entrare con solo Alfa libera)")
            result = True
        else:
            print(f"   ❌ FAIL: Next player è {backend.next_player_alfa_bravo_id}")
            print(f"            Dovrebbe essere None")
            result = False

        return result

    finally:
        cleanup_test_db(db_path)


def test_scenario_4():
    """
    Test Scenario 4: Track Set 2 - stessa logica

    Verifica che la correzione funzioni anche per Track Set 2
    """
    print("\n" + "="*70)
    print("TEST SCENARIO 4: Track Set 2 - logica corretta")
    print("="*70)

    db_path = setup_test_db()

    try:
        backend = GameBackend()

        # Setup
        print("\n1. Setup code Track Set 2:")
        backend.add_couple2('ROSA-001', 'Coppia2 1')
        backend.add_couple2('ROSA-002', 'Coppia2 2')
        backend.add_single2('BIANCO-001', 'Singolo2 1')

        print(f"   - Coda Coppie2: {[p['id'] for p in backend.queue_couples2]}")
        print(f"   - Coda Singoli2: {[p['id'] for p in backend.queue_singles2]}")

        # Start coppia2
        print("\n2. Start ROSA-001 (coppia2):")
        backend.start_game2(is_couple=True)
        print(f"   - Alfa2: {backend.current_player_alfa2['id'] if backend.current_player_alfa2 else 'Libera'}")
        print(f"   - Bravo2: {backend.current_player_bravo2['id'] if backend.current_player_bravo2 else 'Libera'}")
        print(f"   - Next player: {backend.next_player_alfa_bravo_id2}")

        # Press third button
        print("\n3. Premi terzo pulsante 2 (libera Alfa2):")
        backend.button_third_pressed2()
        print(f"   - Alfa2: {backend.current_player_alfa2['id'] if backend.current_player_alfa2 else 'Libera'}")
        print(f"   - Bravo2: {backend.current_player_bravo2['id'] if backend.current_player_bravo2 else 'Libera'}")
        print(f"   - Next player: {backend.next_player_alfa_bravo_id2}")

        # Verify
        print("\n4. Verifica:")
        if backend.next_player_alfa_bravo_id2 == 'BIANCO-001':
            print("   ✅ PASS: Next player è BIANCO-001 (singolo2) - CORRETTO!")
            result = True
        else:
            print(f"   ❌ FAIL: Next player è {backend.next_player_alfa_bravo_id2}")
            print(f"            Dovrebbe essere BIANCO-001")
            result = False

        return result

    finally:
        cleanup_test_db(db_path)


def main():
    """Run all queue mixing tests."""
    print("\n" + "="*70)
    print("🧪 TEST SUITE: VERIFICA FIX MESCOLAMENTO CODE")
    print("="*70)

    tests = [
        ("Singolo entra durante coppia", test_scenario_1),
        ("Priorità coppie entrambe libere", test_scenario_2),
        ("Coppia non entra con solo Alfa", test_scenario_3),
        ("Track Set 2 logica corretta", test_scenario_4),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("📊 RISULTATI")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotale: {passed}/{total} test superati")

    if passed == total:
        print("\n🎉 TUTTI I TEST SUPERATI!")
        print("✅ Il problema del mescolamento code è RISOLTO!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test falliti")
        print("❌ Ci sono ancora problemi da risolvere")
        return 1


if __name__ == '__main__':
    exit(main())
