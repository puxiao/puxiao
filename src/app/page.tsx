import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to Puxiao.com!
        </h1>

        <p className={styles.description}>
          {`I'm a Front End Web Developer: `}
          <code className={styles.code}>React,Vue,Threejs,Electron,WebGPU</code>
          <br />
          I wrote some tutorials to share with you.
        </p>

        <div className={styles.grid}>
          <a href="https://github.com/puxiao/react-hook-tutorial" className={styles.card}>
            <h2>react-hook-tutorial &rarr;</h2>
            <p>https://github.com/puxiao/react-hook-tutorial</p>
          </a>

          <a href="https://github.com/puxiao/threejs-tutorial" className={styles.card}>
            <h2>threejs-tutorial &rarr;</h2>
            <p>https://github.com/puxiao/threejs-tutorial</p>
          </a>

          <a
            href="https://github.com/puxiao/webgpu-tutorial"
            className={styles.card}
          >
            <h2>webgpu-tutorial &rarr;</h2>
            <p>https://github.com/puxiao/webgpu-tutorial</p>
          </a>

          <a
            href="https://github.com/puxiao/wgsl-tutorial"
            className={styles.card}
          >
            <h2>wgsl-tutorial &rarr;</h2>
            <p>
              https://github.com/puxiao/wgsl-tutorial
            </p>
          </a>
        </div>
      </main>
    </div>
  );
}
