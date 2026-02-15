from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # 确保 token 随用户状态变化而失效（例如激活后就不能再用）
        return str(user.pk) + str(timestamp) + str(user.is_active)

account_activation_token = AccountActivationTokenGenerator()