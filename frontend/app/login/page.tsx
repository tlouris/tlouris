export default function LoginPage() {
  return (
    <div className="card">
      <h1>Flow Capacity Monitor Login</h1>
      <p>Use seeded account: admin@example.com / admin123</p>
      <form>
        <input placeholder="Email" />
        <input placeholder="Password" type="password" />
        <button type="submit">Sign in</button>
      </form>
    </div>
  );
}
