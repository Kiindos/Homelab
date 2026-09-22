.PHONY: lint fmt validate

lint: fmt-check validate
	yamllint .
	markdownlint-cli2 "**/*.md"
	cd infra/ansible && ansible-lint

fmt:
	tofu fmt -recursive infra/tofu

fmt-check:
	tofu fmt -recursive -check infra/tofu

validate:
	@for d in infra/tofu/*/; do \
	  echo "==> $$d"; \
	  (cd $$d && tofu init -backend=false -input=false >/dev/null && tofu validate) || exit 1; \
	done
