from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("estoque", "0005_loja_saldoestoque"),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="especificacoes",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Detalhes técnicos, voltagem, dimensões, etc.",
            ),
        ),
    ]
