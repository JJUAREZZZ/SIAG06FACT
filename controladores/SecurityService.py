# controladores/securityservice.py
# clase para gestionar la sesion activa del usuario y control de accesos basados en roles

class SecurityService:
    _usuario_actual = None

    @classmethod
    def set_usuario_actual(cls, usuario):
        # establece el usuario logueado en la sesion actual
        cls._usuario_actual = usuario

    @classmethod
    def get_usuario_actual(cls):
        # retorna el usuario logueado o none si no hay sesion
        return cls._usuario_actual

    @classmethod
    def tiene_permiso(cls, permiso_clave):
        # verifica si el usuario logueado tiene el permiso solicitado
        if not cls._usuario_actual:
            return False
        
        rol = cls._usuario_actual.get("rol")
        # administrador tiene acceso absoluto
        if rol == "Administrador":
            return True
            
        # consultar permisos en la base de datos para otros roles
        try:
            from modelos.usuario_model import UsuarioModel
            model = UsuarioModel()
            return model.verificar_permiso_rol(rol, permiso_clave)
        except Exception:
            return False

    @classmethod
    def obtener_indices_permitidos(cls):
        # retorna los indices de stacked widget del menu principal que estan permitidos
        if not cls._usuario_actual:
            return []
            
        rol = cls._usuario_actual.get("rol")
        if rol == "Administrador":
            return [0, 1, 2, 3, 4, 5]
        elif rol == "Operador":
            # operador puede usar todo
            return [0, 1, 2, 3, 4, 5]
        elif rol == "Usuario":
            # usuario comun solo puede usar facturacion directa
            return [1]
        return []
