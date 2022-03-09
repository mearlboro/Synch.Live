let
  mach-nix = import (builtins.fetchGit {
    url = "https://github.com/DavHau/mach-nix/";
    #rev = "31b21203a1350bff7c541e9dfdd4e07f76d874be"; # master
    ref = "refs/tags/3.4.0";
  }) {
    python = "python39Full";
  };

  imutils = mach-nix.buildPythonPackage {
    src = builtins.fetchGit{
      url = "https://github.com/PyImageSearch/imutils";
      ref = "master";
      # rev = "put_commit_hash_here";
    };
    requirements = ''
      setuptools
    '';
  };

in
mach-nix.buildPythonPackage {
  src = ./.;
  pname = "synch.live";
  version = "0.0.1";

  propagatedBuildInputs = [
    imutils
    mach-nix.nixpkgs.jdk8_headless
  ];

  # NOTE: use master / own version of imutils
  requirements = builtins.replaceStrings [ "imutils" ] [ "" ] 
    (builtins.readFile ./camera/requirements.txt);
}
