# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) since version 2.0.0.

## [Unreleased]
### Added
- Added changelog.
- Added option to [configure default routes](https://jakubtesarek.github.io/trickster/configuration.html#default-routes).
- Added endpoint to [reset all routes to default](/trickster/api/endpoints.html#post-internalreset)

### Fixed
- Increment route and response usage counter before applying delay.

## [2.0.0-alpha] - 2021-03-26
### Added
- Prefix of internal endpoints and port can be configured using both CLI and docker.

## [1.0.7] - 2021-03-24
### Added
- User can specify url prefix of internal routes when using CLI tool.
- Delay can now be specified as single fixed value.
- Added MIT licence

### Changed
- No delay is returned as 0.0 instead of null.

### Fixed
- Greatly improved docker image build speed and result size (900MB -> 170MB).
- Fixed authentication that was removed by accident in one of previous versions.

## [1.0.6] - 2021-03-21
### Added
- Automated [documentation](https://jakubtesarek.github.io/trickster/) deployment to Github pages.
- Added Route property [`is_active`](https://jakubtesarek.github.io/trickster/api/model.html#is_active).
- Added [`/internal/health` endpoint](https://jakubtesarek.github.io/trickster/api/endpoints.html#get-internalhealth).
- Added [`/internal/routes/<route_id>/responses` endpoint](https://jakubtesarek.github.io/trickster/api/endpoints.html#get-internalroutesstringroute_idresponses).

### Changed
- Makefile replaced by [Click CLI utility](https://jakubtesarek.github.io/trickster/cli-utils.html).
- Trickster now runs in Gunicorn inside Docker.
- [Route doesn't match any request if it's not active](https://jakubtesarek.github.io/trickster/api/#how-routes-are-resolving).

### Security
- Added security scanner Github action.
- Added [security notice](https://github.com/JakubTesarek/trickster/blob/main/SECURITY.md).

## [1.0.5] - 2021-03-21
### Fixed
- Fixed github action to release to dockerhub.

## [1.0.4] - 2021-03-20
### Changed
- Completely reworked internal API.

### Added
- Added endpoint to update Route.

## [1.0.3] - 2021-03-20
### Changed
- Completely reworked internal API.

### Added
- Added endpoint to update Route.

## [1.0.2] - 2021-03-16
### Added
- Added unit tests.


## [1.0.1] - 2021-03-15
### Added
- Setup CI/CD using Github actions

## [1.0.0] - 2021-03-15
### Changed
- Remove support for Python <= 3.7
