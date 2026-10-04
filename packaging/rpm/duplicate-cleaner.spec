Name:           duplicate-cleaner
Version:        0.1.0
Release:        1%{?dist}
Summary:        KDE-friendly duplicate file cleaner
License:        MIT
URL:            https://example.invalid/duplicate-cleaner
Source0:        duplicate_cleaner-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  desktop-file-utils
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
Requires:       python3
Requires:       python3-pyside6
Requires:       qt6-qtdeclarative
Requires:       qt6-qtquickcontrols2
Requires:       qt6-qtpdf
Requires:       xdg-utils

%description
Duplicate Cleaner is a KDE-friendly desktop application for finding and deleting duplicate files.

%prep
%autosetup -n duplicate_cleaner-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
install -Dm0644 packaging/rpm/duplicate-cleaner.desktop %{buildroot}%{_datadir}/applications/duplicate-cleaner.desktop
install -Dm0644 packaging/assets/duplicate-cleaner.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/duplicate-cleaner.svg

%check
desktop-file-validate packaging/rpm/duplicate-cleaner.desktop

%files
%doc README.md
%{_bindir}/duplicate-cleaner
%{python3_sitelib}/duplicate_cleaner/
%{python3_sitelib}/duplicate_cleaner-*.dist-info/
%{_datadir}/applications/duplicate-cleaner.desktop
%{_datadir}/icons/hicolor/scalable/apps/duplicate-cleaner.svg

%changelog
* Sun Mar 15 2026 Codex <codex@example.invalid> - 0.1.0-1
- Initial RPM packaging
