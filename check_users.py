import sqlite3
import os

def repair_etat_civil_sql():
    """Réparation directe via SQLite sans passer par SQLAlchemy"""
    
    db_path = 'instance/daaras.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Analyse de la base de données...")
        
        # 1. Vérifier la structure de la table
        cursor.execute("PRAGMA table_info(enseignants)")
        colonnes = cursor.fetchall()
        print("Structure de la table enseignants:")
        for col in colonnes:
            print(f"  - {col[1]} ({col[2]})")
        
        # 2. Vérifier les valeurs d'état civil (en brut)
        cursor.execute("SELECT etat_civil FROM enseignants")
        etats_bruts = cursor.fetchall()
        print(f"\n📊 Valeurs brutes d'état civil ({len(etats_bruts)} enregistrements):")
        for etat in etats_bruts:
            print(f"  - {repr(etat[0])}")
        
        # 3. Réparer les valeurs problématiques
        print("\n🔧 Réparation des valeurs...")
        
        corrections = [
            ("Célibataire", "CELIBATAIRE"),
            ("MARIE(E)", "MARIE"),
            ("DIVORCE(E)", "DIVORCE"), 
            ("VEUF(VE)", "VEUF"),
            ("Marié(e)", "MARIE"),
            ("Divorcé(e)", "DIVORCE"),
            ("Veuf/Veuve", "VEUF")
        ]
        
        total_corrections = 0
        for ancien, nouveau in corrections:
            cursor.execute("UPDATE enseignants SET etat_civil = ? WHERE etat_civil = ?", (nouveau, ancien))
            count = cursor.rowcount
            if count > 0:
                print(f"  - '{ancien}' -> '{nouveau}': {count} correction(s)")
                total_corrections += count
        
        # 4. Valider
        conn.commit()
        print(f"\n✅ {total_corrections} correction(s) appliquée(s)")
        
        # 5. Vérifier le résultat
        cursor.execute("SELECT DISTINCT etat_civil FROM enseignants ORDER BY etat_civil")
        etats_apres = cursor.fetchall()
        print(f"\n🎯 États civils après correction ({len(etats_apres)} valeurs distinctes):")
        for etat in etats_apres:
            print(f"  - {etat[0]}")
            
        # 6. Afficher tous les enseignants
        cursor.execute("SELECT id, matricule, nom, prenom, etat_civil FROM enseignants")
        enseignants = cursor.fetchall()
        print(f"\n👨‍🏫 Liste des enseignants ({len(enseignants)}):")
        for ens in enseignants:
            print(f"  - {ens[1]}: {ens[3]} {ens[2]} ({ens[4]})")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    repair_etat_civil_sql()