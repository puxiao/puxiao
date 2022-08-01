import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Home.module.css'

export default function Home() {
  return (
    <div className={styles.container}>
      <Head>
        <title>Puxiao.com</title>
        <meta name="description" content="Hello world." />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to Puxiao.com!
        </h1>

        <p className={styles.description}>
        {`I'm a Front End Web Developer: `}
          <code className={styles.code}>React,Threejs,Antd,Electron,WebGPU</code>
          <br/>
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

      <footer className={styles.footer}>
        <a
          href="https://vercel.com?utm_source=create-next-app&utm_medium=default-template&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          Powered by{' '}
          <span className={styles.logo}>
            <Image src="/vercel.svg" alt="Vercel Logo" width={72} height={16} />
          </span>
        </a>
      </footer>
    </div>
  )
}
