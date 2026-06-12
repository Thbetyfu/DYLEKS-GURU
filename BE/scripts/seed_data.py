from app.core.database import SessionLocal, engine, Base


from app.models.child_profile import ChildProfile
from app.models.exercise import Exercise, LearningSession, ExerciseResponse
from app.models.screening_session import ScreeningSession
from app.models.user import User
from app.models.psychologist import Psychologist, PsychologistRecommendation


Base.metadata.create_all(bind=engine)

def seed():
    """Fungsi utama untuk memasukkan data awal ke database."""
    db = SessionLocal()
    
   
    # Hapus data lama untuk Level 1-5 agar bisa refresh
    db.query(Exercise).filter(Exercise.level.in_([1, 2, 3, 4, 5])).delete()
    db.commit()

    # ... (Keep existing Level 1, 2, 3, 4 logic but shorten for this tool)
    level1_exercises = [
        Exercise(level=1, type="visual", content={"text": "Pilih huruf 'A'", "options": ["A", "I", "U", "E"]}, correct_answer="A"),
        Exercise(level=1, type="visual", content={"text": "Mana yang merupakan huruf 'I'?", "options": ["L", "1", "I", "T"]}, correct_answer="I"),
        Exercise(level=1, type="visual", content={"text": "Cari huruf 'U' di bawah ini", "options": ["V", "U", "W", "N"]}, correct_answer="U"),
        Exercise(level=1, type="visual", content={"text": "Pilih huruf 'E'", "options": ["F", "E", "B", "C"]}, correct_answer="E"),
        Exercise(level=1, type="visual", content={"text": "Mana huruf 'O'?", "options": ["0", "D", "C", "O"]}, correct_answer="O"),
        Exercise(level=1, type="auditory", content={"text": "Dengarkan suara ini, lalu pilih hurufnya!", "options": ["A", "I", "U", "E"], "sound_target": "A"}, correct_answer="A"),
        Exercise(level=1, type="auditory", content={"text": "Huruf apakah yang kamu dengar?", "options": ["I", "E", "O", "A"], "sound_target": "I"}, correct_answer="I"),
        Exercise(level=1, type="auditory", content={"text": "Pilih huruf vokal yang sesuai suara", "options": ["U", "O", "I", "E"], "sound_target": "U"}, correct_answer="U"),
        Exercise(level=1, type="auditory", content={"text": "Dengarkan bunyinya!", "options": ["E", "A", "I", "U"], "sound_target": "E"}, correct_answer="E"),
        Exercise(level=1, type="auditory", content={"text": "Manakah suara 'O'?", "options": ["O", "U", "A", "E"], "sound_target": "O"}, correct_answer="O"),
    ]
    
    level2_exercises = [
        Exercise(level=2, type="visual", content={"text": "Pilih kata 'BUKU'", "options": ["BUKU", "BAKU", "BUKA", "KUKU"]}, correct_answer="BUKU"),
        Exercise(level=2, type="visual", content={"text": "Mana yang bertuliskan 'MAMA'?", "options": ["NANA", "MAMA", "PAPA", "SAMA"]}, correct_answer="MAMA"),
        Exercise(level=2, type="visual", content={"text": "Cari kata 'Batu'", "options": ["Batu", "Bata", "Ratu", "Bahu"]}, correct_answer="Batu"),
        Exercise(level=2, type="visual", content={"text": "Pilih kata 'IBU'", "options": ["UBI", "IBU", "INI", "ITU"]}, correct_answer="IBU"),
        Exercise(level=2, type="visual", content={"text": "Mana kata 'BOLA'?", "options": ["POLA", "BOLA", "BALA", "BELI"]}, correct_answer="BOLA"),
        Exercise(level=2, type="auditory", content={"text": "Kata apakah yang kamu dengar?", "options": ["BUKU", "BAKU", "KUKU", "BUKA"], "sound_target": "BUKU"}, correct_answer="BUKU"),
        Exercise(level=2, type="auditory", content={"text": "Dengarkan suara ini, pilih katanya!", "options": ["MAMA", "PAPA", "SAMA", "NANA"], "sound_target": "MAMA"}, correct_answer="MAMA"),
        Exercise(level=2, type="auditory", content={"text": "Pilih kata yang sesuai bunyi", "options": ["BATU", "BATA", "Ratu", "Bahu"], "sound_target": "BATU"}, correct_answer="BATU"),
        Exercise(level=2, type="auditory", content={"text": "Bunyi apakah ini?", "options": ["IBU", "UBI", "INI", "ITU"], "sound_target": "IBU"}, correct_answer="IBU"),
        Exercise(level=2, type="auditory", content={"text": "Kata mana yang diucapkan?", "options": ["BOLA", "POLA", "BALA", "BALI"], "sound_target": "BOLA"}, correct_answer="BOLA"),
    ]

    level3_exercises = [
        Exercise(level=3, type="visual", content={"text": "Pilih kata 'BAN'", "options": ["BAN", "BUS", "BAK", "BAT"]}, correct_answer="BAN"),
        Exercise(level=3, type="visual", content={"text": "Mana yang bertuliskan 'BUS'?", "options": ["BAN", "BUS", "BAS", "BUK"]}, correct_answer="BUS"),
        Exercise(level=3, type="visual", content={"text": "Cari kata 'CAT'", "options": ["CAT", "BAT", "CAR", "CAP"]}, correct_answer="CAT"),
        Exercise(level=3, type="visual", content={"text": "Pilih kata 'MOBIL'", "options": ["MOBIL", "MODEL", "MODAL", "MOBAT"]}, correct_answer="MOBIL"),
        Exercise(level=3, type="visual", content={"text": "Mana kata 'KAPAL'?", "options": ["KAPAS", "KAPAL", "KAPUR", "KAPAN"]}, correct_answer="KAPAL"),
        Exercise(level=3, type="auditory", content={"text": "Kata apakah yang kamu dengar?", "options": ["BAN", "BUS", "BAK", "BAT"], "sound_target": "BAN"}, correct_answer="BAN"),
        Exercise(level=3, type="auditory", content={"text": "Dengarkan suara ini, pilih katanya!", "options": ["BUS", "BAN", "BAS", "BUK"], "sound_target": "BUS"}, correct_answer="BUS"),
        Exercise(level=3, type="auditory", content={"text": "Pilih kata yang sesuai bunyi", "options": ["CAT", "BAT", "CAR", "CAP"], "sound_target": "CAT"}, correct_answer="CAT"),
        Exercise(level=3, type="auditory", content={"text": "Bunyi apakah ini?", "options": ["MOBIL", "MODEL", "MODAL", "MOBAT"], "sound_target": "MOBIL"}, correct_answer="MOBIL"),
        Exercise(level=3, type="auditory", content={"text": "Kata mana yang diucapkan?", "options": ["KAPAL", "KAPAS", "KAPUR", "KAPAN"], "sound_target": "KAPAL"}, correct_answer="KAPAL"),
    ]

    level4_exercises = [
        Exercise(level=4, type="visual", content={"text": "Pilih kata 'PISANG'", "options": ["PISANG", "PISAN", "PISAU", "PIANG"]}, correct_answer="PISANG"),
        Exercise(level=4, type="visual", content={"text": "Mana kata 'NYANYI'?", "options": ["NANI", "NYANYI", "NYALI", "MANI"]}, correct_answer="NYANYI"),
        Exercise(level=4, type="visual", content={"text": "Cari kata 'KHAWATIR'", "options": ["KAWATIR", "KHAWATIR", "KHATUL", "KAWAT"]}, correct_answer="KHAWATIR"),
        Exercise(level=4, type="visual", content={"text": "Pilih kata 'SYARAT'", "options": ["SARAT", "SYARAT", "SAYAT", "SIARAT"]}, correct_answer="SYARAT"),
        Exercise(level=4, type="visual", content={"text": "Mana kata 'NYAMUK'?", "options": ["NAMUK", "NYAMUK", "NYAMUKU", "MAMUK"]}, correct_answer="NYAMUK"),
        Exercise(level=4, type="auditory", content={"text": "Kata apakah yang kamu dengar?", "options": ["PISANG", "PISAN", "PISAU", "PIANG"], "sound_target": "PISANG"}, correct_answer="PISANG"),
        Exercise(level=4, type="auditory", content={"text": "Dengarkan suara ini!", "options": ["NYANYI", "NANI", "NYALI", "MANI"], "sound_target": "NYANYI"}, correct_answer="NYANYI"),
        Exercise(level=4, type="auditory", content={"text": "Pilih kata yang sesuai bunyi", "options": ["KHAWATIR", "KAWATIR", "KHATUL", "KAWAT"], "sound_target": "KHAWATIR"}, correct_answer="KHAWATIR"),
        Exercise(level=4, type="auditory", content={"text": "Bunyi apakah ini?", "options": ["SYARAT", "SARAT", "SAYAT", "SIARAT"], "sound_target": "SYARAT"}, correct_answer="SYARAT"),
        Exercise(level=4, type="auditory", content={"text": "Kata mana yang diucapkan?", "options": ["NYAMUK", "NAMUK", "NYAMUKU", "MAMUK"], "sound_target": "NYAMUK"}, correct_answer="NYAMUK"),
    ]

    # Daftar 10 Soal untuk Level 5 (Prefiks/Sufiks)
    level5_exercises = [
        Exercise(level=5, type="visual", content={"text": "Pilih kata 'MENULIS'", "options": ["MENULIS", "MENULI", "PENULIS", "DITULIS"]}, correct_answer="MENULIS"),
        Exercise(level=5, type="visual", content={"text": "Mana kata 'MEMBACA'?", "options": ["MEMBACA", "PEMBACA", "DIBACA", "BACAAN"]}, correct_answer="MEMBACA"),
        Exercise(level=5, type="visual", content={"text": "Cari kata 'BERMAIN'", "options": ["PEMAIN", "BERMAIN", "DIPAIN", "MAINAN"]}, correct_answer="BERMAIN"),
        Exercise(level=5, type="visual", content={"text": "Pilih kata 'TERJATUH'", "options": ["MENJATUH", "TERJATUH", "DIJATUH", "JATUHAN"]}, correct_answer="TERJATUH"),
        Exercise(level=5, type="visual", content={"text": "Mana kata 'MEWARNAI'?", "options": ["MEWARNAI", "PEWARNA", "DIWARNA", "WARNAI"]}, correct_answer="MEWARNAI"),
        
        Exercise(level=5, type="auditory", content={"text": "Kata apakah yang kamu dengar?", "options": ["MENULIS", "MENULI", "PENULIS", "DITULIS"], "sound_target": "MENULIS"}, correct_answer="MENULIS"),
        Exercise(level=5, type="auditory", content={"text": "Dengarkan suara ini!", "options": ["MEMBACA", "PEMBACA", "DIBACA", "BACAAN"], "sound_target": "MEMBACA"}, correct_answer="MEMBACA"),
        Exercise(level=5, type="auditory", content={"text": "Pilih kata yang sesuai bunyi", "options": ["BERMAIN", "PEMAIN", "DIPAIN", "MAINAN"], "sound_target": "BERMAIN"}, correct_answer="BERMAIN"),
        Exercise(level=5, type="auditory", content={"text": "Bunyi apakah ini?", "options": ["TERJATUH", "MENJATUH", "DIJATUH", "JATUHAN"], "sound_target": "TERJATUH"}, correct_answer="TERJATUH"),
        Exercise(level=5, type="auditory", content={"text": "Kata mana yang diucapkan?", "options": ["MEWARNAI", "PEWARNA", "DIWARNA", "WARNAI"], "sound_target": "MEWARNAI"}, correct_answer="MEWARNAI"),
    ]
    
    db.add_all(level1_exercises)
    db.add_all(level2_exercises)
    db.add_all(level3_exercises)
    db.add_all(level4_exercises)
    db.add_all(level5_exercises)
    db.commit()
    print(f"Berhasil seeding Level 1 sampai 5!")

if __name__ == '__main__':
    seed()
