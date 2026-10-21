Name:           duplicate-cleaner
Version:        0.1.0
Release:        1%{?dist}
Summary:        Cross-platform duplicate file cleaner
License:        MIT
URL:            https://github.com/isojanis/duplicate_cleaner
Source0:        duplicate_cleaner-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  desktop-file-utils
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-build
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
Requires:       python3
Requires:       python3-pyside6
Requires:       qt6-qtdeclarative
Requires:       qt6-qtpdf
Requires:       qt6-qtsvg
Requires:       xdg-utils

%description
Duplicate Cleaner is a Qt desktop application for finding identical files on Linux and Windows.

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
%doc README.md THIRD_PARTY_NOTICES LICENSE_AUDIT.md
%license LICENSE LICENSES
%{_bindir}/duplicate-cleaner
%{python3_sitelib}/duplicate_cleaner/
%{python3_sitelib}/duplicate_cleaner-*.dist-info/
%{_datadir}/applications/duplicate-cleaner.desktop
%{_datadir}/icons/hicolor/scalable/apps/duplicate-cleaner.svg
