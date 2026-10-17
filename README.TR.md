# Storytold

**Yerel yaratıcı çalışma. Yerel uygulama motorları. Doğrulanmış dosya
aktarımları.**

Açık kaynaklı ArtCraft **Craft App Suite** için bir Claude Code ve Codex
eklentisi: tek bir `craft` Skill'i, on üç yerel, başsız (headless) Craft MCP
uygulamasını (fotoğraf, vektör, video, RAW, PDF, mizanpaj, hesap tablosu, belge,
sunum, CAD, ses, hareketli grafik ve arayüz tasarımı) hazırlanmış kopyalar ve
doğrulanmış dışa aktarımlar üzerinden yönetir.

[![CI](https://github.com/devsolux/storytold/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/devsolux/storytold/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/devsolux/storytold)](https://github.com/devsolux/storytold/releases/latest)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English](README.md) · [Deutsch](README.DE.md) · **Türkçe**

> **Teşekkürler, ArtCraft ekibi!** Storytold, [ArtCraft](https://getartcraft.com/)
> ekibinin ücretsiz ve açık kaynaklı yazılım olarak yayımladığı Craft App Suite
> üzerine kuruludur: her biri sıfırdan yazılmış on üç yaratıcı uygulama. Bu
> cömertlik için minnettarız. Onların emeği olmasaydı bu entegrasyon var
> olmazdı.
>
> ❤️ **ArtCraft ekibi** 💚

## İçindekiler

- [Genel bakış](#genel-bakış)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Craft App Suite uygulamaları](#craft-app-suite-uygulamaları)
- [Yerel uygulamaların kurulumu](#yerel-uygulamaların-kurulumu)
- [Güncelleme ve kaldırma](#güncelleme-ve-kaldırma)
- [Neler nerede](#neler-nerede)
- [Güvenli çalışma](#güvenli-çalışma)
- [Geliştirme](#geliştirme)
- [Doğrulama durumu](#doğrulama-durumu)
- [Depo haritası](#depo-haritası)
- [Lisans ve bağlılık](#lisans-ve-bağlılık)

## Genel bakış

Storytold, Devsolux'un on üç mevcut Craft CLI MCP sunucusu için yerel
entegrasyon kitidir. Küçük bir `craft` Skill'i host'u yönlendirir; her uygulama
kendi şemalarını, düzenleme durumunu, render ve kaydetme davranışını korur.
Deterministik yardımcılar CLI'leri yalnızca açık komutla kurar ve sabitler,
dosyaları hazırlar, kanıta bağlı yapılandırma üretir ve yapıtları belirtilen
sınırlar içinde doğrular.

```text
Kullanıcı + Claude Code / yerel Codex
           │  tek craft Skill'i; yerel araç keşfi ve onaylar
           ├── stdio ── PhotoCraft, VectorCraft, FilmCraft, LightCraft
           ├── stdio ── PdfCraft, EffectCraft, DesignCraft, GridCraft
           ├── stdio ── WordCraft, DeckCraft, CADCraft, SoundCraft
           └── stdio ── FigCraft
                                │
                      yerel motorlar → kalıcı dosyalar
```

**Ne olduğu**

- Tek bir yönlendirici Skill, gerektiğinde yüklenen on üç uygulama kartı ve iki
  iş akışı rehberi.
- Uygulama ve host başına bir tane olmak üzere on üç doğrudan, yerel stdio MCP
  kaydı.
- Craft CLI'lerini kuran, doğrulayan, sabitleyen, yoklayan ve kaydeden, yalnızca
  standart kütüphaneyle yazılmış bir Python CLI'si (`storytold.py`); ama yalnızca
  siz çalıştırdığınızda.

**Ne olmadığı**

- Ağ geçidi MCP sunucusu, arka plan hizmeti (daemon), yönlendirici ya da ikinci
  bir yapay zekâ ajanı yoktur.
- Pakete dahil ikili dosya yoktur: eklentiyi kurmak rehberi, gözden geçirilmiş
  sürüm manifestini ve pasif şablonları ekler; asla çalıştırılabilir dosya, izin
  ya da çalışan MCP süreci eklemez.
- Uzak bir ChatGPT bağlayıcısı değildir. Yerel Codex desteği ek bir paketleme ve
  yapılandırma uyarlamasıdır.
- Bir işletim sistemi sanal alanı (sandbox) değildir. Bkz.
  [Güvenli çalışma](#güvenli-çalışma) ve [SECURITY.md](SECURITY.md).

## Hızlı başlangıç

**1. Eklentiyi kurun.** Depo `devsolux/storytold`, eklenti `storytold`, pazar
yeri `devsolux-storytold`. Her iki host da **plugin@marketplace** biçimini
kullanır:

```bash
claude plugin marketplace add https://github.com/devsolux/storytold
claude plugin install storytold@devsolux-storytold

codex plugin marketplace add devsolux/storytold
codex plugin add storytold@devsolux-storytold
```

**2. Yerel uygulamaları kurun.** Bir klondan ya da kurulu eklenti dizininden
(`~/.claude` veya `~/.codex` altında
`<home>/plugins/cache/devsolux-storytold/storytold/<version>/`) tek bir
uygulamayı ya da on üçünü birden kurun:

```bash
python3 storytold.py setup --app photocraft
```

```bash
python3 storytold.py setup --all --acknowledge-unconfined
```

**3. Yeni bir host oturumu başlatın** ve Skill'i kullanın: Claude Code'da
`/storytold:craft`, Codex'te ise Skill seçicisinden `storytold:craft`.

`python3 storytold.py doctor` her uygulama için bulduğu masaüstü uygulamasını,
CLI'yi ve host kaydını bildirir ve eksik olan her şey için tam `setup` komutunu
yazdırır; bir sunucu bağlı değilken Skill aynı komutu sohbette önerir.

## Craft App Suite uygulamaları

ArtCraft Launcher, **Craft App Suite**'i kurar: [ArtCraft](https://getartcraft.com/)
ekibinin her biri Rust ile sıfırdan yazılmış, her biri tek başına
kullanılabilen ücretsiz ve açık kaynaklı yaratıcı araçları. **Dosya erişimi**
sütunu, Storytold'un her uygulamanın MCP sunucusunu nasıl başlattığını gösterir.

| | Uygulama | Ne için | Dosya erişimi | Kod | Daha fazlası |
|:-:|---|---|---|---|---|
| <img src="https://raw.githubusercontent.com/storytold/photocraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.photocraft.png" alt="" width="32" height="32"> | **PhotoCraft** | Görüntü düzenleme: katmanlar, maskeler, yazı ve gerçek PSD dosyaları | Okuma/yazma kökleri | [GitHub](https://github.com/storytold/photocraft) | [Web sitesi](https://getartcraft.com/apps/photocraft) |
| <img src="https://raw.githubusercontent.com/storytold/vectorcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.vectorcraft.png" alt="" width="32" height="32"> | **VectorCraft** | Vektör illüstrasyon | Okuma/yazma kökleri | [GitHub](https://github.com/storytold/vectorcraft) | [Web sitesi](https://getartcraft.com/apps/vectorcraft) |
| <img src="https://raw.githubusercontent.com/storytold/filmcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.filmcraft.png" alt="" width="32" height="32"> | **FilmCraft** | Video kurgu, renk ve ses | Kullanıcı geneli | [GitHub](https://github.com/storytold/filmcraft) | [Web sitesi](https://getartcraft.com/apps/filmcraft) |
| <img src="https://raw.githubusercontent.com/storytold/lightcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.lightcraft.png" alt="" width="32" height="32"> | **LightCraft** | Fotoğraf kütüphanesi ve RAW geliştirme | Kullanıcı geneli | [GitHub](https://github.com/storytold/lightcraft) | [Web sitesi](https://getartcraft.com/apps/lightcraft) |
| <img src="https://raw.githubusercontent.com/storytold/pdfcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.pdfcraft.png" alt="" width="32" height="32"> | **PdfCraft** | PDF okuma, düzenleme ve koruma | Tek kök | [GitHub](https://github.com/storytold/pdfcraft) | [Web sitesi](https://getartcraft.com/apps/pdfcraft) |
| <img src="https://raw.githubusercontent.com/storytold/effectcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.effectcraft.png" alt="" width="32" height="32"> | **EffectCraft** | Hareketli grafik ve görsel efektler | Okuma/yazma kökleri | [GitHub](https://github.com/storytold/effectcraft) | [Web sitesi](https://getartcraft.com/apps/effectcraft) |
| <img src="https://raw.githubusercontent.com/storytold/designcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.designcraft.png" alt="" width="32" height="32"> | **DesignCraft** | Sayfa mizanpajı ve yayıncılık | Kullanıcı geneli | [GitHub](https://github.com/storytold/designcraft) | [Web sitesi](https://getartcraft.com/apps/designcraft) |
| <img src="https://raw.githubusercontent.com/storytold/gridcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.gridcraft.png" alt="" width="32" height="32"> | **GridCraft** | Hesap tabloları ve veri | Kullanıcı geneli | [GitHub](https://github.com/storytold/gridcraft) | [Web sitesi](https://getartcraft.com/apps/gridcraft) |
| <img src="https://raw.githubusercontent.com/storytold/wordcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.wordcraft.png" alt="" width="32" height="32"> | **WordCraft** | Kelime işlem ve belgeler | Okuma/yazma kökleri | [GitHub](https://github.com/storytold/wordcraft) | [Web sitesi](https://getartcraft.com/apps/wordcraft) |
| <img src="https://raw.githubusercontent.com/storytold/deckcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.deckcraft.png" alt="" width="32" height="32"> | **DeckCraft** | Sunumlar ve slaytlar | Kullanıcı geneli | [GitHub](https://github.com/storytold/deckcraft) | [Web sitesi](https://getartcraft.com/apps/deckcraft) |
| <img src="https://raw.githubusercontent.com/storytold/cadcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.cadcraft.png" alt="" width="32" height="32"> | **CADCraft** | Bilgisayar destekli tasarım (CAD) | Kullanıcı geneli | [GitHub](https://github.com/storytold/cadcraft) | [Web sitesi](https://getartcraft.com/apps/cadcraft) |
| <img src="https://raw.githubusercontent.com/storytold/soundcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.soundcraft.png" alt="" width="32" height="32"> | **SoundCraft** | Ses kaydı ve düzenleme | Okuma/yazma kökleri | [GitHub](https://github.com/storytold/soundcraft) | [Web sitesi](https://getartcraft.com/apps/soundcraft) |
| <img src="https://raw.githubusercontent.com/storytold/figcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.figcraft.png" alt="" width="32" height="32"> | **FigCraft** | Arayüz tasarımı ve prototipleme | Kullanıcı geneli | [GitHub](https://github.com/storytold/figcraft) | [Web sitesi](https://getartcraft.com/apps/figcraft) |

- **Okuma/yazma kökleri** (beş uygulama): çalışma alanını okumalarına ve
  yalnızca onun `outputs/` dizinine yazmalarına izin veren yerel kök
  bayraklarıyla başlatılır.
- **Tek kök** (PdfCraft): `inputs/` dâhil tüm çalışma alanını kapsayan tek bir
  kök; ayrı okuma/yazma sınırlaması değildir.
- **Kullanıcı geneli** (yedi uygulama): dosya kökü bayrağı yoktur, bu yüzden
  işletim sistemi kullanıcınızın erişebildiği her şeyi okuyup yazabilir.
  `setup` bunları yalnızca `--acknowledge-unconfined` ile kurar ve kaydeder;
  onları hassas olmayan işler için kullanın ya da işletim sistemi yalıtımı
  altında çalıştırın.

## Yerel uygulamaların kurulumu

Her uygulamanın MCP sunucusu kendi CLI'sidir: `<app>-cli`. Ne eklenti ne de
masaüstü uygulaması onu sağlar ya da kaydeder; kurulana kadar Skill,
uygulamanın yerel araçlarının bağlı olmadığını haklı olarak bildirir. `setup`,
macOS (universal), Linux x86_64 ve Windows x64'ü destekler ve Python 3.11+
gerektirir.

### `setup` ne yapar

Seçilen her uygulama için `setup` şu adımları izler:

1. Platformunuz için [`config/releases.json`](config/releases.json) içinde
   sabitlenmiş arşivi (macOS CLI zip'i, Linux tarball'ı ya da Windows
   taşınabilir zip'i) indirir.
2. Onu bu manifeste **ve** sürümün kendi `SHA256SUMS.txt` dosyasına karşı
   denetler, ardından içinden yalnızca tek `<app>-cli` dosyasını çıkarır.
3. Kaynağını doğrular (bkz. [Kaynak doğrulama](#kaynak-doğrulama)).
4. Adayı etkin kurulumun yanında hazırlar ve ona karşı preflight'ı ve resmi MCP
   SDK yoklamasını çalıştırır: initialize, tools/list ve tek bir salt okunur
   çağrı.
5. Ancak ondan sonra onu `~/.local/opt/craft/bin` konumuna (Windows'ta
   `%LOCALAPPDATA%\Storytold\craft\bin`) yükseltir ve ikili dosyanın özetini
   özel bir kilide sabitler.
6. Sunucuyu PATH'teki her host CLI'sine kaydeder (`codex mcp add`,
   `claude mcp add --scope user`).

Herhangi bir adımda başarısız olan bir aday, önceki ikili dosyayı,
sabitlemesini ve kayıtları olduğu gibi bırakır; dosya değiştirme ile kilidin
yeniden yazılması arasında kesilen bir yükseltmeyi bir sonraki çalıştırma
tutarlı duruma getirir. `setup`'ı yeniden çalıştırmak idempotenttir: kurulu
ikili dosyası sabitlemesiyle ve manifestle eşleşen bir uygulama atlanır,
eşleşen bir kayıt korunur. Siz çağırmadıkça hiçbir şey çalışmaz. Ardından yeni
bir host oturumu başlatın.

### Seçenekler

| Seçenek | Etkisi |
|---|---|
| `--app <app>` / `--all` | Tek bir uygulamayı (tekrarlanabilir) ya da on üçünün tamamını seçer. |
| `--acknowledge-unconfined` | Kullanıcı genelindeki yedi uygulamayı da kurar ve kaydeder. Yalıtım kanıtı değildir. |
| `--host {codex,claude}` | Yalnızca belirtilen host'a kaydeder (varsayılan: PATH'teki her host CLI'si); PATH'te olmayan belirtilmiş bir host çalıştırmayı başarısız kılar. |
| `--dry-run` | Gerçek bir çalıştırmanın her uygulama için ne yapacağını (`keep`, `install`, `upgrade`, `skip` veya `refuse`, yalnızca gerektiğinde indirme, her kayıt) ve başarılı olup olmayacağını ya da `--remove` ile birlikte tam olarak neyin kaldırılacağını önizler. Hiçbir şeyi değiştirmez. |
| `--list` | Manifest, kurulum, sabitleme ve kayıt durumunu ve kullanılan yolları gösterir. |
| `--upgrade` | Sabitlemesi değişen bir uygulamayı manifest sürümüne taşır. |
| `--replace` | Başka bir yere işaret eden aynı adlı sunucuyu yeniden kaydeder; yenisi eklenemezse eski kayıt geri getirilir. |
| `--remove` | Yalnızca `setup`'ın kendi yazdığı kullanıcı kapsamı kayıtlarını (aynı komut ve argümanlar, uygulama hâlâ sabitlenmiş) kaldırır ve yalnızca baytları kilitle eşleşen ve hiçbir host'ta kalan bir kaydın artık başlatmadığı bir ikili dosyayı siler; geri kalan her şey raporlanır ve korunur. |
| `--skip-probe` | İkili dosyayı çalıştırmadan kaydeder ve bunu belirtir. |
| `--trust-upstream-sums` | Linux/Windows: Sigstore paketi ya da cosign yokken yalnızca manifest ve `SHA256SUMS.txt` ile ilerler; bu, kilide kaydedilir. |

`python3 storytold.py setup --help` kalan yol ve zaman aşımı geçersiz
kılmalarını listeler. Diğer platformlar, ağdan yalıtılmış makineler ve özel
sabitlemeler [işletim](docs/operations.md) belgesindeki elle yapılan zinciri
kullanır: indirme, kilit, `preflight`, `probe`, `configure`, kayıt.

### Kaynak doğrulama

macOS'ta ikili dosya ArtCraft ekibi tarafından Apple noterliğinden geçirilmiş
olmalıdır. Upstream, Linux ve Windows derlemelerini kod imzalamaz; bu yüzden
[günlük iş akışı](.github/workflows/releases.yml) sabitlenmiş her CLI'yi kendi
GitHub kimliğiyle, anahtarsız olarak [Sigstore cosign](https://docs.sigstore.dev/)
ile imzalar ve paketleri [`config/signatures.json`](config/signatures.json)
dosyasına işler. Linux ve Windows'ta `setup` kurmadan önce bu paketi
`cosign verify-blob` ile doğrular (önce cosign'ı kurun); cosign varsa macOS da
doğrular. Bir sürümün paketi olmadığında ya da cosign yokken
`--trust-upstream-sums` yalnızca manifest ve `SHA256SUMS.txt` ile ilerler ve
bunu kilide yazar.

### Günlük sürüm yenileme

İş akışı her gün her uygulamanın son sürümünü denetler, manifesti yeniden
yazar, yeni CLI'leri imzalar, eklentiyi yeniden derler, denetimleri ve gerçek
`setup`'ı Linux, Windows ve macOS runner'larında çalıştırır ve inceleme için
`bot/releases` üzerinde tek bir çekme isteği açar (yeşil çalıştırmaları otomatik
birleştirmek için depo değişkeni `STORYTOLD_AUTO_MERGE=true` olarak ayarlanır).
Kullanıcılar yeni sabitlemeleri bir sonraki eklenti güncellemesiyle alır.

## Güncelleme ve kaldırma

### Güncelleme

Güncelleme iki adımdan oluşur. Önce eklentiyi güncelleyin:

```bash
claude plugin marketplace update devsolux-storytold
claude plugin update storytold@devsolux-storytold

codex plugin marketplace upgrade devsolux-storytold
codex plugin add storytold@devsolux-storytold
```

Codex'te `plugin update` yoktur: `marketplace upgrade` Git anlık görüntüsünü
yeniler, `plugin add` yeniden çalıştırıldığında yeni sürümü oradan kurar. Bir
eklenti güncellemesi Skill'i, belgeleri ve yenilenmiş sürüm manifestini getirir;
kurulu CLI'lere ve host kayıtlarına asla dokunmaz ve eklenti dizini artık yeni
sürüm numarasını taşır.

Ardından Craft CLI'lerini ilerletin. `--list` hangi sabitlemelerin değiştiğini
gösterir (`manifest_commit_pinned: false`); `--all --upgrade` yalnızca o
uygulamaları yeniden indirir, doğrular ve yeniden yoklar, kayıtları olduğu gibi
bırakır:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --list
```

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --all --upgrade --acknowledge-unconfined
```

Bir sürüm bir uygulamanın başlatma argümanlarını değiştirdiğinde (1.5.0'da
WordCraft'ın, 1.5.2'de SoundCraft'ın kök bayrakları), farklı kaydın yeniden
yazılması için `--replace` ekleyin; o olmadan `setup` farkı yalnızca bildirir ve
kaydı olduğu gibi bırakır. SoundCraft köklerine yalnızca 0.7.0'dan itibaren
uyar; bu yüzden daha eski bir kurulu SoundCraft,
`setup --app soundcraft --upgrade --replace` onu güncelleyene kadar reddedilir.

### Kaldırma

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --remove --all
claude plugin uninstall storytold@devsolux-storytold
codex plugin remove storytold@devsolux-storytold
```

`setup --remove --all` önce Storytold'un yönettiği on üç CLI'nin kaydını
kaldırır, ikili dosyaları ve sabitlemeleri siler. Çalışma alanı ve çıktılar
kalır; kilidin Storytold tarafından kurulduğunu kanıtlayamadığı hiçbir şey de
silinmez. Yalnızca eklentiyi kaldırmak sunucuları kayıtlı ve çalışır durumda
bırakır.

### Kaynak kopyasından kurulum

Üretilen `plugins/storytold/` çalışma zamanı depoya işlenmiştir; bu yüzden her
iki host da doğrudan herkese açık depodan kurar ve kurulum sırasında hiçbir şey
derlenmez. Kaynak kopyasından `make install-claude-local` ya da
`make install-codex-local` bunun yerine yerel pazar yerini kurar. Bu hedefler
host durumunu değiştirir; derlemeler ve testler bunları asla çalıştırmaz. Host
paketleme ve kurulum kaynakları [kaynak defterinde](docs/source-ledger.md)
kayıtlıdır.

## Neler nerede

Eklenti dizini yalnızca kod, belge ve sürüm manifestini içerir. `setup`
kurduğu her şeyi onun dışında tutar, böylece bir eklenti güncellemesi ya da
kaldırması hiçbir zaman bir CLI'yi silemez, geri alamaz ya da değiştiremez ve
tek bir kurulu kopya her iki host'a da hizmet eder. `python3 storytold.py
setup --list` kullanılan yolları yazdırır.

| Nerede (macOS/Linux) | Windows | Ne | Kim yazar |
|---|---|---|---|
| `~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/`, `~/.claude` altında da aynı | `%USERPROFILE%` altında aynı | Eklenti: `craft` Skill'i, belgeler, `storytold.py`, `config/releases.json`, `config/signatures.json`. İkili dosya yok. | `codex plugin add` / `claude plugin install` |
| `~/.local/opt/craft/bin/` | `%LOCALAPPDATA%\Storytold\craft\bin\` | On üç Craft CLI'si (`photocraft-cli` … `figcraft-cli`, her biri 16–192 MB). Her iki host da bunları başlatır, örn. `…/cadcraft-cli mcp`. | `setup` |
| `~/.local/state/storytold/` (Linux'ta `$XDG_STATE_HOME/storytold`) | `%LOCALAPPDATA%\Storytold\state\` | Özel durum: `installations.lock.json` (sabitlenmiş özetler), `evidence/` (uygulama başına yoklama makbuzları), `venv/` (yoklama için resmi MCP SDK), `setup.json` (kaydedilen yollar). | `setup` |
| `~/craft-work-storytold/` | `%USERPROFILE%\craft-work-storytold\` | Çalışma alanı: `inputs/`, `outputs/` (dışa aktarımlar buraya düşer), `receipts/`. | `setup` oluşturur; uygulamalar `outputs/` dizinini doldurur |
| `~/.codex/config.toml` ve `~/.claude.json` | aynı | Uygulama ve host başına, yukarıdaki mutlak CLI yoluna işaret eden tek bir kullanıcı kapsamlı MCP kaydı. | `codex mcp add`, `claude mcp add --scope user`; `setup` çalıştırır |

Tam Unix başlatma şablonları `config/` altındadır; yalnızca örnektirler, etkin
host yapılandırması değildir. Gerçek yapılandırma üretimi yerel Windows'ta
`.exe` seçer ve ortam değişkeni genişletmesinin her host'ta aynı çalışmasına
güvenmek yerine somut, doğrulanmış yollar yazar. Makineye özgü yapılandırma
paketlerin dışında kalır.

## Güvenli çalışma

Her görev aynı döngüyü izler:

**İncele → hazırlanmış kopya → yerel düzenleme → önizleme → kaydet/dışa aktar
→ yeniden aç/doğrula.**

- **Uygulama kartları.** [On üç uygulama kartı](skills/craft/SKILL.md)
  uygulamaya özgü tuzakları anlatır: VectorCraft'ta başsız seçim, LightCraft
  kütüphane kilitleri, PdfCraft'ta açık kaydetme, DesignCraft UTF-8 bayt
  konumları, GridCraft'ta tipli formüller, FigCraft'ta sayfa birimleri, medya
  zamanlaması ve çevrimdışı uyarıları. Bunlar kaynaktan türetilmiş ipuçlarıdır;
  bağlı ikili dosya geçerli API'yi sağlar.
- **Uygulamalar arası çalışma.** Doğrulanmış dosyaları aktarın, asla başka bir
  sunucunun bellek içi kimliklerini değil. PhotoCraft, DesignCraft için PNG;
  DesignCraft, PdfCraft için PDF dışa aktarabilir. Bir aşama başarısız olursa
  son doğrulanmış yapıtta durun. Evrensel toplu işlem, otomatik yazma yinelemesi
  ya da gizli yedek yol vaat edilmez.
- **Sınırlama.** Kök bayrakları, Skill, yoklama makbuzları ve MCP yapılandırması
  bir işletim sistemi sanal alanı değildir; host'un diğer kabuk ve dosya araçları
  da uygun izinlere ihtiyaç duyar. Ticari kullanım, [kabul](docs/acceptance.md)
  belgesindeki yerel aşamaları ve [SECURITY.md](SECURITY.md) içindeki önlemleri
  gerektirir.

## Geliştirme

Python **3.11+** çekirdek araçları ve testleri çalıştırır; GNU Make isteğe
bağlı bir kolaylıktır. Varsayılan denetimler ve derleme için üçüncü taraf
Python paketi ya da ağ erişimi gerekmez.

```bash
make check
make test
make build
make verify-build
```

| Hedef | Amaç |
|---|---|
| `make help` | Tüm hedefleri listeler; hiçbir şey kurmaz ya da başlatmaz. |
| `make doctor` | Host'ları ya da yerel uygulamaları başlatmadan kurulu yetenekleri bildirir. |
| `make check` | Kaynakları, bağlantıları, kimlikleri, kataloğu, örnekleri ve pasif paketlemeyi doğrular. |
| `make test` | Tüm çekirdek testleri yalıtılmış bir kaynak kopyasında çalıştırır; ağ ya da yerel ikili dosya kullanmaz. |
| `make build` / `make verify-build` | Ortak eklentiyi izin listesindeki kanonik dosyalardan üretir, ardından sapmaya karşı denetler. |
| `make package` / `make source` | Deterministik eklenti ZIP'ini ve eksiksiz kaynak ZIP'ini, her birini sağlama toplamıyla oluşturur. |
| `make release` | Sıralı denetimler, çekirdek testler ve yeniden üretilebilir paketleme; yayımlama ya da yerel kabul iddiası yoktur. |
| `make setup` / `make setup-probe` | Yerel bir `.venv` oluşturur; ardından açık bir ağ tercihi olarak özet kilitli resmi MCP SDK'yı (`mcp==2.3.0`) kurar. |
| `make test-sdk` | Gerçek SDK'yı Craft uygulamalarına değil, sentetik bir stdio fikstürüne karşı sınar. |
| `make refresh-releases` / `make sign-releases` | Günlük iş akışının çalıştırdığı ağ adımları (imzalama cosign gerektirir). |
| `make setup-confined` | Kök sınırlı altı uygulamayı bu makinede kurar, sabitler, yoklar ve kaydeder. |
| `make clean` | Yalnızca işaretli `.build/` ve `dist/` dizinlerini kaldırır; çalışma alanları ve `.venv` kalır. |

Derlemeler ve testler asla commit, push ya da kurulum yapmaz; yalnızca adıyla
çağrılan `make github-*` hedefleri commit ya da push yapar. [Makefile](Makefile)
tüm hedefleri listeler, [CONTRIBUTING.md](CONTRIBUTING.md) katkı kurallarını
açıklar.

## Doğrulama durumu

Çevrimdışı çekirdek testleri, resmi MCP SDK sözleşme testi, sıkı Claude
manifest doğrulaması ve Skill keşfiyle Claude Code ve Codex kurulumu
çalıştırıldı. `setup`, on üç Craft CLI'sinin tamamını macOS, Linux ve Windows
runner'larında kurdu, yokladı ve Sigstore ile doğruladı; on ikisini ayrıca bir
geliştirici Mac'inde. Bu, protokol düzeyinde bir kanıttır, yerel kabul değildir:
[kabul](docs/acceptance.md) belgesindeki aşamaları çalıştırmak işletmeciye
kalır. [Doğrulama raporu](docs/verification.md), her sürüm için gerçekten
çalıştırılanları belgesel kanıttan ayırır.

## Depo haritası

| Yol | Sorumluluk |
|---|---|
| `skills/craft/` | Tek yönlendirici Skill, on üç uygulama kartı ve iki iş akışı |
| `config/` | Gözden geçirilmiş başlatma kataloğu, sürüm manifesti ve Sigstore paket deposu, pasif şablonlar, örnek kilit ve ortam |
| `storytold_tools/`, `storytold.py` | Deterministik CLI ve isteğe bağlı kısa ömürlü SDK yoklaması |
| `scripts/`, `Makefile` | Çevrimdışı denetimler, testler, korumalı derlemeler ve paketleme |
| `tests/` | Çekirdek regresyon testleri, sentetik SDK fikstürü, yerel kabul senaryoları |
| `docs/` | Mimari, işletim, kabul, kaynaklar ve doğrulama |
| `plugins/storytold/` | Üretilen ortak çalışma zamanı; asla doğrudan düzenlemeyin |
| `.github/workflows/` | Çevrimdışı CI matrisi ile günlük sürüm yenileme, imzalama ve üç işletim sisteminde doğrulama |

[Mimari](docs/architecture.md), yerel planın neden eski ağ geçidi
referansından önce geldiğini ve hangi bileşenin neye sahip olduğunu kayda
geçirir.

## Lisans ve bağlılık

[MIT Lisansı](LICENSE) ile yayımlanmıştır. Yerel uygulamalar, SDK'lar, yazı
tipleri ve medya pakete dahil değildir ve kendi lisanslarını korur; bkz.
[lisans bildirimi](LICENSE-NOTICE.md).

Storytold bir Devsolux entegrasyonudur. Upstream `storytold` organizasyonu,
Anthropic ya da OpenAI ile bir bağlılık ya da onay iddia edilmez.
