import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import styles from "./home.module.css";

export default function HomePage() {
  return (
    <>
      <AppHeader />
      <main id="main" className={styles.hero}>
        <p className={styles.brand}>MyWave Event App</p>
        <h1 className={styles.headline}>Соревнования под контролем</h1>
        <p className={styles.lead}>
          Единая цифровая сцена для участников, судей и организаторов — без привязки к сайту
          MyWave.
        </p>
        <div className={styles.ctaGroup}>
          <Link href="/login" className={styles.ctaPrimary}>
            Войти по телефону
          </Link>
          <Link href="/register" className={styles.ctaSecondary}>
            Зарегистрироваться
          </Link>
          <Link href="/events" className={styles.ctaSecondary}>
            Смотреть события
          </Link>
        </div>
      </main>
    </>
  );
}
