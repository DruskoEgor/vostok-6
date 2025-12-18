import krpc, time, math


class VostokMission:
    def __init__(self):
        self.conn = None
        self.vessel = None
        self.ap = None
        self.space_center = None
        self.start_time = None
        self.orbit_period = 2208

    def connect(self):
        try:
            self.conn = krpc.connect(name='Vostok')
            self.space_center = self.conn.space_center
            self.vessel = self.space_center.active_vessel
            self.ap = self.vessel.auto_pilot
            print("=" * 60)
            print("МИССИЯ ВОСТОК - 6")
            print("=" * 60)
            return True
        except:
            return False

    def launch(self):
        print("\n✓ РАКЕТА ВЗЛЕТЕЛА!")
        self.ap.engage()
        self.ap.target_pitch_and_heading(90, 90)
        self.vessel.control.throttle = 1.0
        time.sleep(2)
        self.vessel.control.activate_next_stage()
        self.start_time = time.time()

    def gravity_turn(self):
        stage1, stage2 = False, False
        while True:
            alt = self.vessel.flight().mean_altitude
            orbit = self.vessel.orbit
            apo, peri = orbit.apoapsis_altitude, orbit.periapsis_altitude

            if time.time() - self.start_time >= 100 and not stage1:
                print("✓ ОТДЕЛЕНИЕ 1-Й СТУПЕНИ")
                self.vessel.control.throttle = 0.0
                time.sleep(0.2)
                self.vessel.control.activate_next_stage()
                time.sleep(0.5)
                self.vessel.control.throttle = 1.0
                time.sleep(0.2)
                self.vessel.control.activate_next_stage()
                stage1 = True

            if alt < 5000:
                target = 90
            elif alt < 30000:
                target = 85
            elif alt < 70000:
                target = 45
            else:
                target = -15
            self.ap.target_pitch_and_heading(target, 90)

            if not stage2 and 220000 <= apo <= 240000 and peri > 0:
                self.vessel.control.throttle = 0.0
                time.sleep(1)
                print("✓ ОТДЕЛЕНИЕ 2-Й СТУПЕНИ")
                self.vessel.control.activate_next_stage()
                time.sleep(2)
                self.orbit_period = orbit.period
                print(f"✓ ВЫХОД НА ОРБИТУ: Апоцентр {apo / 1000:.0f}км, Перицентр {peri / 1000:.0f}км")
                return True
            time.sleep(0.1)

    def wait_48_orbits(self):
        print("✓ ОЖИДАНИЕ 48 ВИТКОВ...")
        orbit_start = self.space_center.ut
        self.space_center.rails_warp_factor = 6
        while self.space_center.ut - orbit_start < 48 * self.orbit_period:
            time.sleep(1)
        self.space_center.rails_warp_factor = 0
        time.sleep(2)
        print("✓ 48 ВИТКОВ ЗАВЕРШЕНЫ")

    def brake_and_descend(self):
        print("✓ ТОРМОЖЕНИЕ ДЛЯ ПРИЗЕМЛЕНИЯ")

        # Ориентация на ретроград
        self.ap.reference_frame = self.vessel.orbital_reference_frame
        self.ap.target_direction = (0, -1, 0)
        time.sleep(5)

        # Включение 3-й ступени
        print("✓ ВКЛЮЧЕНИЕ ДВИГАТЕЛЯ")
        self.vessel.control.activate_next_stage()
        self.vessel.control.throttle = 1.0

        # Отсчет 5 секунд
        for i in range(5, 0, -1):
            time.sleep(1)
        print()

        # Выключение двигателя 3-й ступени
        self.vessel.control.throttle = 0.0
        print("✓ ВЫКЛЮЧЕНИЕ ДВИГАТЕЛЯ 3-Й СТУПЕНИ")
        time.sleep(2)

        # Отделение 3-й ступени (командный модуль отделяется)
        print("✓ ОТДЕЛЕНИЕ ПОСЛЕДНЕЙ СТУПЕНИ")
        self.vessel.control.activate_next_stage()
        time.sleep(2)

        # Проверка новой орбиты
        orbit = self.vessel.orbit
        print(
            f"✓ НОВАЯ ОРБИТА: Апоапсис {orbit.apoapsis_altitude / 1000:.0f}км, Периапсис {orbit.periapsis_altitude / 1000:.0f}км")
        print("✓  РАКЕТА УПАДЕТ НА ЗЕМЛЮ" if orbit.periapsis_altitude < 0 else "✓  ОРБИТА СТАБИЛЬНА")

        # Включение варпа 4 уровня для ускорения спуска
        print("✓ ВКЛЮЧЕНИЕ ВАРПА 4 УРОВНЯ")
        self.space_center.rails_warp_factor = 4

        print("⬇ СПУСК В АТМОСФЕРЕ")
        while True:
            alt = self.vessel.flight().surface_altitude
            if alt <= 2000:
                # Выключение варпа перед раскрытием парашюта
                self.space_center.rails_warp_factor = 0
                time.sleep(1)
                print("✓ РАСКРЫТИЕ ПАРАШЮТА НА 2000 МЕТРАХ")

                # Пробуем несколько методов раскрытия парашюта
                try:
                    # Метод 1: Через API
                    parachutes = self.vessel.parts.parachutes
                    if parachutes:
                        for parachute in parachutes:
                            if not parachute.deployed:
                                parachute.deploy()
                                print("✓ ПАРАШЮТ РАСКРЫТ ЧЕРЕЗ API!")
                    else:
                        # Метод 2: Активация стадии
                        self.vessel.control.activate_next_stage()
                except:
                    # Метод 3: Резервный
                    self.vessel.control.activate_next_stage()

                # Ждем приземления
                while alt > 10:
                    alt = self.vessel.flight().surface_altitude
                    speed = abs(self.vessel.flight().vertical_speed)
                    print(f"Высота: {alt:.0f}м, Скорость: {speed:.1f}м/с", end='\r')
                    time.sleep(1)
                print()
                print("✓ ПРИЗЕМЛЕНИЕ УСПЕШНОЕ")
                return True

            # Показываем прогресс спуска
            if int(time.time()) % 5 == 0:
                print(f"Высота: {alt:.0f}м", end='\r')

            time.sleep(0.1)

    def run(self):
        if not self.connect(): return

        try:
            self.launch()
            self.gravity_turn()
            self.wait_48_orbits()
            self.brake_and_descend()
            print("\n" + "=" * 60)
            print("МИССИЯ ВОСТОК-6 УСПЕШНО ЗАВЕРШЕНА!")
            print("=" * 60)
        except KeyboardInterrupt:
            print("\n Миссия прервана")
            self.vessel.control.throttle = 0.0
            if self.ap: self.ap.disengage()
        except Exception as e:
            print(f"\n Ошибка: {e}")
            self.vessel.control.throttle = 0.0
            if self.ap: self.ap.disengage()


def main():
    print("Запуск")

    mission = VostokMission()
    mission.run()


if __name__ == "__main__":
    main()
