import unittest
import os
from app_clinica import app, db, User
from werkzeug.security import generate_password_hash

class AuthTestCase(unittest.TestCase):
    """Conjunto de testes para autenticação e gerenciamento de usuários."""

    def setUp(self):
        """
        Configura um ambiente de teste antes de cada teste.
        - Usa um banco de dados em memória.
        - Cria um cliente de teste.
        - Cria as tabelas do banco.
        - Adiciona usuários padrão (admin e esteta).
        """
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Desabilita CSRF para testes
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Garante que a chave secreta esteja definida para testes de flash messages
        app.config['SECRET_KEY'] = 'my-test-secret-key'
        
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Criar usuários para os testes
            admin_user = User(
                username='test_admin', 
                password_hash=generate_password_hash('AdminPassword1!'), 
                perfil='admin'
            )
            esteta_user = User(
                username='test_esteta', 
                password_hash=generate_password_hash('EstetaPassword1!'), 
                perfil='esteta'
            )
            db.session.add(admin_user)
            db.session.add(esteta_user)
            db.session.commit()

    def tearDown(self):
        """
        Limpa o ambiente de teste após cada teste.
        - Remove a sessão do banco.
        - Apaga todas as tabelas.
        """
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # --- Testes de Login e Logout ---

    def test_login_page(self):
        """Testa se a página de login é carregada corretamente."""
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fazer Login', response.data)

    def test_login_logout_success(self):
        """Testa o fluxo completo de login e logout com sucesso."""
        # Tenta fazer login
        response = self.app.post('/login', data=dict(
            username='test_admin',
            password='AdminPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard do Administrador', response.data)
        self.assertIn(b'test_admin', response.data) # Verifica se o nome de usuário aparece

        # Tenta fazer logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fazer Login', response.data)
        self.assertIn(b'Voc\xc3\xaa saiu da sua conta.', response.data) # "Você saiu da sua conta."

    def test_login_invalid_credentials(self):
        """Testa o login com credenciais inválidas."""
        response = self.app.post('/login', data=dict(
            username='test_admin',
            password='wrongpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Usu\xc3\xa1rio ou senha inv\xc3\xa1lidos.', response.data) # "Usuário ou senha inválidos."

    # --- Testes de Registro ---

    def test_registro_page(self):
        """Testa se a página de registro é carregada."""
        response = self.app.get('/registro', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Criar Nova Conta', response.data)

    def test_registro_success(self):
        """Testa o registro de um novo usuário com sucesso."""
        response = self.app.post('/registro', data=dict(
            username='new_user',
            password='NewPassword1!',
            password_confirm='NewPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'criado com sucesso', response.data)
        # Verifica se o usuário foi criado no banco com o perfil padrão 'esteta'
        with app.app_context():
            user = User.query.filter_by(username='new_user').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.perfil, 'esteta')

    def test_registro_usuario_existente(self):
        """Testa o registro com um nome de usuário que já existe."""
        response = self.app.post('/registro', data=dict(
            username='test_admin',
            password='NewPassword1!',
            password_confirm='NewPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Este usu\xc3\xa1rio j\xc3\xa1 existe.', response.data) # "Este usuário já existe."

    def test_registro_senhas_nao_correspondem(self):
        """Testa o registro com senhas que não correspondem."""
        response = self.app.post('/registro', data=dict(
            username='another_user',
            password='NewPassword1!',
            password_confirm='DifferentPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'As senhas n\xc3\xa3o correspondem.', response.data) # "As senhas não correspondem."

    def test_registro_senha_fraca(self):
        """Testa o registro com uma senha fraca."""
        response = self.app.post('/registro', data=dict(
            username='weak_user',
            password='123',
            password_confirm='123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'A senha deve ter pelo menos 8 caracteres', response.data)

    # --- Testes de Gerenciamento de Usuários (Admin) ---

    def login_admin(self):
        """Função auxiliar para logar como admin."""
        return self.app.post('/login', data=dict(
            username='test_admin',
            password='AdminPassword1!'
        ), follow_redirects=True)

    def test_gerenciar_usuarios_sem_permissao(self):
        """Testa o acesso à página de gerenciamento por um usuário não-admin."""
        # Loga como esteta
        self.app.post('/login', data=dict(username='test_esteta', password='EstetaPassword1!'), follow_redirects=True)
        response = self.app.get('/gerenciar-usuarios', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Voc\xc3\xaa n\xc3\xa3o tem permiss\xc3\xa3o', response.data) # "Você não tem permissão"
        self.assertNotIn(b'Gerenciar Usu\xc3\xa1rios', response.data) # "Gerenciar Usuários"

    def test_gerenciar_usuarios_com_permissao_admin(self):
        """Testa o acesso à página de gerenciamento por um admin."""
        self.login_admin()
        response = self.app.get('/gerenciar-usuarios', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gerenciar Usu\xc3\xa1rios', response.data)
        self.assertIn(b'test_admin', response.data)
        self.assertIn(b'test_esteta', response.data)

    def test_admin_cria_usuario_com_perfil(self):
        """Testa se um admin pode criar um usuário com um perfil específico."""
        self.login_admin()
        response = self.app.post('/registro', data=dict(
            username='secretaria_user',
            password='SecretariaPassword1!',
            password_confirm='SecretariaPassword1!',
            perfil='secretaria'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redireciona para o login
        self.assertIn(b'criado com sucesso! Perfil: SECRETARIA', response.data)
        
        with app.app_context():
            user = User.query.filter_by(username='secretaria_user').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.perfil, 'secretaria')

    def test_admin_altera_perfil_usuario(self):
        """Testa se um admin pode alterar o perfil de outro usuário."""
        self.login_admin()
        with app.app_context():
            user_to_change = User.query.filter_by(username='test_esteta').first()
            user_id = user_to_change.id

        response = self.app.post(f'/usuarios/{user_id}/alterar-perfil/secretaria', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Perfil de &#39;test_esteta&#39; alterado para SECRETARIA.", response.data)

        with app.app_context():
            changed_user = db.session.get(User, user_id)
            self.assertEqual(changed_user.perfil, 'secretaria')

    def test_admin_nao_pode_alterar_proprio_perfil(self):
        """Testa se um admin não pode alterar seu próprio perfil."""
        self.login_admin()
        with app.app_context():
            admin_user = User.query.filter_by(username='test_admin').first()
            admin_id = admin_user.id

        response = self.app.post(f'/usuarios/{admin_id}/alterar-perfil/esteta', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Voc\xc3\xaa n\xc3\xa3o pode alterar seu pr\xc3\xb3prio perfil.', response.data) # "Você não pode alterar seu próprio perfil."

    def test_admin_deleta_usuario(self):
        """Testa se um admin pode deletar outro usuário."""
        self.login_admin()
        with app.app_context():
            user_to_delete = User.query.filter_by(username='test_esteta').first()
            user_id = user_to_delete.id

        response = self.app.post(f'/usuarios/{user_id}/deletar', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Usu\xc3\xa1rio &#39;test_esteta&#39; deletado com sucesso.", response.data) # "Usuário 'test_esteta' deletado com sucesso."

        with app.app_context():
            deleted_user = db.session.get(User, user_id)
            self.assertIsNone(deleted_user)

    def test_admin_nao_pode_deletar_a_si_mesmo(self):
        """Testa se um admin não pode deletar a própria conta."""
        self.login_admin()
        with app.app_context():
            admin_user = User.query.filter_by(username='test_admin').first()
            admin_id = admin_user.id

        response = self.app.post(f'/usuarios/{admin_id}/deletar', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Voc\xc3\xaa n\xc3\xa3o pode deletar sua pr\xc3\xb3pria conta.', response.data) # "Você não pode deletar sua própria conta."

    # --- Testes da Página de Perfil ---

    def test_perfil_page_acesso_negado(self):
        """Testa que a página de perfil redireciona se não estiver logado."""
        response = self.app.get('/perfil', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Por favor, fa\xc3\xa7a login para acessar esta p\xc3\xa1gina.', response.data) # "Por favor, faça login para acessar esta página."

    def test_perfil_alterar_senha_sucesso(self):
        """Testa a alteração de senha com sucesso."""
        self.login_admin()
        response = self.app.post('/perfil', data=dict(
            senha_atual='AdminPassword1!',
            nova_senha='NewAdminPassword1!',
            confirmar_senha='NewAdminPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sua senha foi alterada com sucesso!', response.data)

        # Tenta logar com a nova senha
        self.app.get('/logout', follow_redirects=True) # Logout
        response_new_login = self.app.post('/login', data=dict(
            username='test_admin',
            password='NewAdminPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response_new_login.status_code, 200)
        self.assertIn(b'Dashboard do Administrador', response_new_login.data)

    def test_perfil_senha_atual_incorreta(self):
        """Testa a alteração de senha com a senha atual incorreta."""
        self.login_admin()
        response = self.app.post('/perfil', data=dict(
            senha_atual='wrongpassword',
            nova_senha='NewAdminPassword1!',
            confirmar_senha='NewAdminPassword1!'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sua senha atual est\xc3\xa1 incorreta.', response.data) # "Sua senha atual está incorreta."

if __name__ == '__main__':
    unittest.main()