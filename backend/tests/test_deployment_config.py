from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_nginx_port_template_is_outside_active_conf_directory():
    """Only the rendered Nginx config may be loaded from conf.d."""
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")
    entrypoint = (REPOSITORY_ROOT / "docker-entrypoint.sh").read_text(encoding="utf-8")

    template_path = "/etc/nginx/default.conf.template"
    rendered_path = "/etc/nginx/conf.d/default.conf"

    assert f"COPY nginx.combined.conf {template_path}" in dockerfile
    assert f"{template_path} > {rendered_path}" in entrypoint
    assert "/etc/nginx/conf.d/default.template.conf" not in dockerfile
    assert "/etc/nginx/conf.d/default.template.conf" not in entrypoint
