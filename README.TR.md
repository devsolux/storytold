# Storytold

Açık kaynaklı ArtCraft Craft App Suite için Claude Code ve Codex eklentisi: tek
bir `craft` Skill'i, hazırlanmış kopyalar ve doğrulanmış dışa aktarımlarla 12
yerel, başsız (headless) Craft MCP uygulamasını (fotoğraf, vektör, video, RAW,
PDF, mizanpaj, tablo, belge, sunum, CAD, ses, hareketli grafik) yönetir.

[English](README.md) · [Deutsch](README.DE.md) · **Türkçe**

> **Teşekkürler, ArtCraft ekibi!** Storytold, [ArtCraft](https://getartcraft.com/)
> ekibinin ücretsiz ve açık kaynaklı yazılım olarak yayımladığı Craft App Suite
> üzerine kuruludur: her biri sıfırdan yazılmış on iki yaratıcı uygulama. Bu
> cömertlik için minnettarız. Onların emeği olmasaydı bu entegrasyon var
> olmazdı.
>
> ❤️ **ArtCraft ekibi** 💚

**Yerel yaratıcı çalışma. Yerel uygulama motorları. Doğrulanmış dosya
aktarımları.**

Storytold, Devsolux'un on iki mevcut Craft CLI MCP sunucusu için yerel
entegrasyon kitidir. Küçük bir `craft` Skill'i host'u yönlendirir; uygulamalar
kendi şemalarını, düzenleme durumlarını, render ve kaydetme davranışlarını
korur. Deterministik yardımcılar on iki CLI'yi yalnızca açık komutla kurar ve
sabitler, dosyaları hazırlar, kanıta bağlı yapılandırma üretir ve yapıtları
belirtilen sınırlar içinde doğrular. **On üçüncü bir MCP sunucusu ya da ikinci
bir yapay zekâ ajanı yoktur.**

```text
Kullanıcı + Claude Code / yerel Codex
           │  tek craft Skill'i; yerel araç keşfi ve onaylar
           ├── stdio ── PhotoCraft, VectorCraft, FilmCraft, LightCraft
           ├── stdio ── PdfCraft, EffectCraft, DesignCraft, GridCraft
           └── stdio ── WordCraft, DeckCraft, CADCraft, SoundCraft
                                │
                      yerel motorlar → kalıcı dosyalar
```

Çevrimdışı çekirdek testleri, resmi MCP SDK sözleşme testi,
sıkı Claude manifest doğrulaması ve Skill keşfiyle Claude Code/Codex kurulumu
çalıştırıldı; `setup`, on iki Craft CLI'nin tamamını macOS, Linux ve Windows
runner'larında ve bir geliştirici Mac'inde kurdu, yokladı ve Sigstore ile
doğruladı; bkz. [doğrulama](docs/verification.md). Craft uygulamaları
pakete dahil değildir: eklentiyi kurmak rehberi, gözden geçirilmiş sürüm
manifestini ve pasif şablonları kurar; asla ikili dosya, izin ya da çalışan MCP
süreci kurmaz. CLI'leri yalnızca aşağıdaki açık `setup` komutu kurar ve kaydeder.
Ticari kullanım, [kabul](docs/acceptance.md) belgesindeki yerel kabul
aşamalarını gerektirir.

## Skill/eklentiyi kurun

Depo `devsolux/storytold` · eklenti `storytold` · pazar yeri
`devsolux-storytold`. Her iki host da **plugin@marketplace** biçimini kullanır:

```bash
claude plugin marketplace add https://github.com/devsolux/storytold
claude plugin install storytold@devsolux-storytold

codex plugin marketplace add devsolux/storytold
codex plugin add storytold@devsolux-storytold
```

Daha sonra güncelleme (2 adımın 1'i):

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
sürüm numarasını taşır. 2 adımın 2'si Craft CLI'lerini ilerletir:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --list
```

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --all --upgrade --acknowledge-unconfined
```

`--list` hangi sabitlemelerin değiştiğini gösterir (`manifest_commit_pinned:
false`); `--all --upgrade` yalnızca o uygulamaları yeniden indirir, doğrular ve
yeniden yoklar, kayıtları olduğu gibi bırakır (komut yolu aynıdır). Kaldırma:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --remove --all
claude plugin uninstall storytold@devsolux-storytold
codex plugin remove storytold@devsolux-storytold
```

`setup --remove --all` önce Storytold'un yönettiği on iki CLI'nin kaydını
kaldırır, ikili dosyaları ve sabitlemeleri siler (çalışma alanı ve çıktılar
kalır; kilidin Storytold tarafından kurulduğunu kanıtlayamadığı hiçbir şey de
silinmez); yalnızca eklentiyi kaldırmak sunucuları kayıtlı ve çalışır durumda
bırakır.

Üretilen `plugins/storytold/` çalışma zamanı depoya işlenmiştir; bu yüzden her
iki host da doğrudan herkese açık depodan kurar, kurulum sırasında hiçbir şey
derlenmez. Kaynak kopyasından `make install-claude-local` ya da
`make install-codex-local` bunun yerine yerel pazar yerini kurar. Bu komutlar
host durumunu değiştirir; derlemeler ve testler bunları asla çalıştırmaz ve
yalnızca açık `make github-*` hedefleri commit ya da push yapar.

Claude Code, Skill'i `/storytold:craft` olarak gösterir; Codex, Skill
seçicisinde `storytold:craft` olarak listeler. Her uygulama için tek bir yerel
MCP kaydı kullanın. Yerel Codex desteği ek bir paketleme/yapılandırma
uyarlamasıdır, uzak bir ChatGPT bağlayıcısı **değildir**. Host paketleme ve
kurulum kaynakları [kaynak defterinde](docs/source-ledger.md) kayıtlıdır.

## Craft App Suite

ArtCraft Launcher, **Craft App Suite**'i kurar: [ArtCraft](https://getartcraft.com/)
ekibinin her biri Rust ile sıfırdan yazılmış, her biri tek başına
kullanılabilen ücretsiz ve açık kaynaklı yaratıcı araçları.

| | Uygulama | Ne için | Kod | Daha fazlası |
|:-:|---|---|---|---|
| <img src="https://raw.githubusercontent.com/storytold/photocraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.photocraft.png" alt="" width="32" height="32"> | **PhotoCraft** | Görüntü düzenleme: katmanlar, maskeler, yazı ve gerçek PSD dosyaları | [GitHub](https://github.com/storytold/photocraft) | [Web sitesi](https://getartcraft.com/apps/photocraft) |
| <img src="https://raw.githubusercontent.com/storytold/vectorcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.vectorcraft.png" alt="" width="32" height="32"> | **VectorCraft** | Vektör illüstrasyon | [GitHub](https://github.com/storytold/vectorcraft) | [Web sitesi](https://getartcraft.com/apps/vectorcraft) |
| <img src="https://raw.githubusercontent.com/storytold/filmcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.filmcraft.png" alt="" width="32" height="32"> | **FilmCraft** | Video kurgu, renk ve ses | [GitHub](https://github.com/storytold/filmcraft) | [Web sitesi](https://getartcraft.com/apps/filmcraft) |
| <img src="https://raw.githubusercontent.com/storytold/lightcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.lightcraft.png" alt="" width="32" height="32"> | **LightCraft** | Fotoğraf kütüphanesi ve RAW geliştirme | [GitHub](https://github.com/storytold/lightcraft) | [Web sitesi](https://getartcraft.com/apps/lightcraft) |
| <img src="https://raw.githubusercontent.com/storytold/pdfcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.pdfcraft.png" alt="" width="32" height="32"> | **PdfCraft** | PDF okuma, düzenleme ve koruma | [GitHub](https://github.com/storytold/pdfcraft) | [Web sitesi](https://getartcraft.com/apps/pdfcraft) |
| <img src="https://raw.githubusercontent.com/storytold/effectcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.effectcraft.png" alt="" width="32" height="32"> | **EffectCraft** | Hareketli grafik ve görsel efektler | [GitHub](https://github.com/storytold/effectcraft) | [Web sitesi](https://getartcraft.com/apps/effectcraft) |
| <img src="https://raw.githubusercontent.com/storytold/designcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.designcraft.png" alt="" width="32" height="32"> | **DesignCraft** | Sayfa mizanpajı ve yayıncılık | [GitHub](https://github.com/storytold/designcraft) | [Web sitesi](https://getartcraft.com/apps/designcraft) |
| <img src="https://raw.githubusercontent.com/storytold/gridcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.gridcraft.png" alt="" width="32" height="32"> | **GridCraft** | Hesap tabloları ve veri | [GitHub](https://github.com/storytold/gridcraft) | [Web sitesi](https://getartcraft.com/apps/gridcraft) |
| <img src="https://raw.githubusercontent.com/storytold/wordcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.wordcraft.png" alt="" width="32" height="32"> | **WordCraft** | Kelime işlem ve belgeler | [GitHub](https://github.com/storytold/wordcraft) | [Web sitesi](https://getartcraft.com/apps/wordcraft) |
| <img src="https://raw.githubusercontent.com/storytold/deckcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.deckcraft.png" alt="" width="32" height="32"> | **DeckCraft** | Sunumlar ve slaytlar | [GitHub](https://github.com/storytold/deckcraft) | [Web sitesi](https://getartcraft.com/apps/deckcraft) |
| <img src="https://raw.githubusercontent.com/storytold/cadcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.cadcraft.png" alt="" width="32" height="32"> | **CADCraft** | Bilgisayar destekli tasarım (CAD) | [GitHub](https://github.com/storytold/cadcraft) | [Web sitesi](https://getartcraft.com/apps/cadcraft) |
| <img src="https://raw.githubusercontent.com/storytold/soundcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.soundcraft.png" alt="" width="32" height="32"> | **SoundCraft** | Ses kaydı ve düzenleme | [GitHub](https://github.com/storytold/soundcraft) | [Web sitesi](https://getartcraft.com/apps/soundcraft) |

## Ağ erişimi olmadan geliştirme

Python **3.11+** çekirdek araçları ve testleri çalıştırır; GNU Make isteğe
bağlı bir kolaylıktır. Varsayılan denetimler ve derleme için üçüncü taraf
Python bağımlılığı gerekmez.

```bash
make help
make doctor
make check
make test
make build
make verify-build
make package
make source
make clean
```

`make setup` yalnızca yerel bir sanal ortam oluşturur. `make setup-probe`,
`mcp==2.3.0` için açık bir ağ tercihidir; ardından `make test-sdk` gerçek
SDK'yı açıkça sentetik bir stdio fikstürüne karşı sınar. On iki Craft
uygulamasını çalıştırmaz. `make release` denetimleri, çekirdek testleri ve
yeniden üretilebilir paketlemeyi sıralar; yerel kabul iddia etmez ve hiçbir
şey yayımlamaz. `make refresh-releases` ve `make sign-releases`, günlük iş
akışının çalıştırdığı ağ adımlarıdır (ikincisi cosign gerektirir);
`make setup-confined` bu makinede kök sınırlı dört uygulamayı kurar.
[Makefile](Makefile) tüm hedefleri listeler.

## Yerel uygulamaları kurun (tek komut)

Her uygulamanın MCP sunucusu kendi CLI'sidir: `<app>-cli`. Eklentiyi ya da
masaüstü uygulamasını kurmak onu ne sağlar ne de kaydeder; o ana kadar Skill,
uygulamanın yerel araçlarının bağlı olmadığını haklı olarak bildirir. Tek bir
açık komut bunu uygulama başına ya da on ikisi için birden çözer; macOS
(universal), Linux x86_64 ve Windows x64'te:

```bash
python3 storytold.py setup --app photocraft
```

```bash
python3 storytold.py setup --all --acknowledge-unconfined
```

Bunu bir klondan ya da her iki host'un da `~/.codex` veya `~/.claude` altında
`<home>/plugins/cache/devsolux-storytold/storytold/<version>/` konumuna
yerleştirdiği kurulu eklenti dizininden çalıştırın; `python3 storytold.py
doctor` eksik her uygulama için doğru yolu içeren tam komutu yazdırır ve bir
sunucu bağlı değilken `craft` Skill'i aynı komutu sohbette önerir. `setup` her
uygulama için platformunuza göre
[`config/releases.json`](config/releases.json) içinde sabitlenmiş arşivi
(macOS CLI zip'i, Linux tarball'ı ya da Windows taşınabilir zip'i) indirir, onu
bu manifeste **ve** sürümün kendi `SHA256SUMS.txt` dosyasına karşı denetler,
içinden yalnızca tek `<app>-cli` dosyasını çıkarır, kaynağını doğrular, etkin
kurulumun yanında hazırlar, preflight'ı ve resmi MCP SDK yoklamasını
(initialize, tools/list, tek bir salt okunur çağrı) bu hazırlanmış adaya karşı
çalıştırır ve ancak ondan sonra onu yükseltir (`~/.local/opt/craft/bin` ya da
Windows'ta `%LOCALAPPDATA%\Storytold\craft\bin`), ikili dosyanın özetini özel
bir kilide sabitler ve sunucuyu PATH'teki her host CLI'sine kaydeder
(`codex mcp add`, `claude mcp add --scope user`). Herhangi bir adımda
başarısız olan bir aday, önceki ikili dosyayı, sabitlemesini ve kayıtları
olduğu gibi bırakır. Ardından yeni bir oturum başlatın. `setup`'ı yeniden çalıştırmak idempotenttir: kurulu ikili dosyası
sabitlemesiyle ve manifestle eşleşen bir uygulama atlanır, zaten eşleşen bir
kayıt korunur. `--dry-run` önizleme yapar; `--list` manifest, kurulum,
sabitleme ve kayıt durumunu gösterir; `--upgrade` sabitlemesi değişen bir
uygulamayı manifest sürümüne taşır; `--replace` başka bir yere işaret eden aynı
adlı sunucuyu yeniden kaydeder ve yenisi eklenemezse eski kaydı geri getirir;
`--skip-probe` ikili dosyayı çalıştırmadan kaydeder ve bunu belirtir;
`--remove` yalnızca `setup`'ın kendi yazdığı kullanıcı kapsamı kayıtlarını
(aynı komut ve argümanlar, uygulama hâlâ sabitlenmiş) kaldırır ve yalnızca
baytları kilitle eşleşen bir ikili dosyayı siler; geri kalan her şey korunur
ve raporlanır. `--remove --dry-run` hiçbir şeyi değiştirmeden tam olarak bunu
önizler. Dosya değiştirme ile kilidin yeniden yazılması arasında kesilen bir
yükseltmeyi bir sonraki çalıştırma tutarlı duruma getirir. Siz çağırmadıkça hiçbir şey çalışmaz; Python 3.11+
gerekir.

**Kaynak doğrulama.** macOS'ta ikili dosya ArtCraft ekibi tarafından Apple
noterliğinden geçirilmiş olmalıdır. Upstream, Linux ve Windows derlemelerini
kod imzalamaz; bu yüzden [günlük iş akışı](.github/workflows/releases.yml)
sabitlenmiş her CLI'yi kendi GitHub kimliğiyle, anahtarsız olarak
[Sigstore cosign](https://docs.sigstore.dev/) ile imzalar ve paketleri
[`config/signatures.json`](config/signatures.json) dosyasına işler; Linux ve
Windows'ta `setup` kurmadan önce bu paketi `cosign verify-blob` ile doğrular
(önce cosign'ı kurun), cosign varsa macOS da doğrular. Bir sürümün paketi
olmadığında ya da cosign yokken `--trust-upstream-sums` yalnızca manifest ve
`SHA256SUMS.txt` ile ilerler ve bunu kilide yazar.

**Günlük yenileme.** İş akışı her gün her uygulamanın son sürümünü denetler,
manifesti yeniden yazar, yeni CLI'leri imzalar, eklentiyi yeniden derler,
denetimleri ve gerçek `setup`'ı Linux, Windows ve macOS runner'larında
çalıştırır ve inceleme için `bot/releases` üzerinde tek bir çekme isteği açar
(yeşil çalıştırmaları otomatik birleştirmek için depo değişkeni
`STORYTOLD_AUTO_MERGE=true` olarak ayarlanır). Kullanıcılar yeni sabitlemeleri
bir sonraki eklenti güncellemesiyle alır.

PhotoCraft, VectorCraft, EffectCraft ve PdfCraft yerel kök bayraklarıyla
çalışma alanına sınırlıdır ve varsayılan olarak kaydedilir. Diğer sekizi
kullanıcınızın erişebildiği her şeyi okuyup yazabilir; bu yüzden yalnızca
`--acknowledge-unconfined` ile kurulur ve kaydedilir: onları hassas olmayan işler için
kullanın ya da işletim sistemi yalıtımı altında çalıştırın. Diğer platformlar,
ağdan yalıtılmış makineler ve özel sabitlemeler
[işletim](docs/operations.md) belgesindeki elle yapılan zinciri kullanır:
indirme, kilit, `preflight`, `probe`, `configure`, kayıt.

## Neler nerede

Eklenti dizini yalnızca kod, belge ve sürüm manifestini içerir; `setup`
kurduğu her şeyi onun dışında tutar, böylece bir eklenti güncellemesi ya da
kaldırması hiçbir zaman bir CLI'yi silemez, geri alamaz ya da değiştiremez ve
tek bir kurulu kopya her iki host'a da hizmet eder. `python3 storytold.py
setup --list` kullanılan yolları yazdırır.

| Nerede (macOS/Linux) | Windows | Ne | Kim yazar |
|---|---|---|---|
| `~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/`, `~/.claude` altında da aynı | `%USERPROFILE%` altında aynı | Eklenti: `craft` Skill'i, belgeler, `storytold.py`, `config/releases.json`, `config/signatures.json`. İkili dosya yok. | `codex plugin add` / `claude plugin install` |
| `~/.local/opt/craft/bin/` | `%LOCALAPPDATA%\Storytold\craft\bin\` | On iki Craft CLI'si (`photocraft-cli` … `soundcraft-cli`, her biri 16–192 MB). Her iki host da bunları başlatır, örn. `…/cadcraft-cli mcp`. | `setup` |
| `~/.local/state/storytold/` (Linux'ta `$XDG_STATE_HOME/storytold`) | `%LOCALAPPDATA%\Storytold\state\` | Özel durum: `installations.lock.json` (sabitlenmiş özetler), `evidence/` (uygulama başına yoklama makbuzları), `venv/` (yoklama için resmi MCP SDK), `setup.json` (kaydedilen yollar). | `setup` |
| `~/craft-work-storytold/` | `%USERPROFILE%\craft-work-storytold\` | Çalışma alanı: `inputs/`, `outputs/` (dışa aktarımlar buraya düşer), `receipts/`. Sınırlı uygulamalar `inputs`'u okur, yalnızca `outputs`'a yazar. | `setup` oluşturur; uygulamalar `outputs`'u doldurur |
| `~/.codex/config.toml` ve `~/.claude.json` | aynı | Uygulama ve host başına, yukarıdaki mutlak CLI yoluna işaret eden tek bir kullanıcı kapsamlı MCP kaydı. | `codex mcp add`, `claude mcp add --scope user`; `setup` çalıştırır |

Tam Unix başlatma şablonları `config/` altındadır. Yalnızca örnektirler, etkin
host yapılandırması değildir. Gerçek yapılandırma üretimi yerel Windows'ta
`.exe` seçer ve ortam değişkeni genişletmesinin her host'ta aynı çalışmasını
ummak yerine somut, doğrulanmış yollar yazar. Makineye özgü yapılandırma
paketlerin dışında kalır.

## Güvenli yaratıcı iş akışı

**İncele → hazırlanmış kopya → yerel düzenleme → önizleme → kaydet/dışa aktar
→ yeniden aç/doğrula.**

[On iki uygulama kartı](skills/craft/SKILL.md) özel tuzakları anlatır:
VectorCraft'ta başsız seçim, LightCraft kütüphane kilitleri, PdfCraft'ta açık
kaydetme, DesignCraft UTF-8 bayt konumları, GridCraft'ta tipli formüller, medya
zamanlaması ve çevrimdışı uyarıları. Bunlar kaynaktan türetilmiş ipuçlarıdır;
bağlı ikili dosya geçerli API'yi sağlar.

Uygulamalar arası çalışmada doğrulanmış dosyaları aktarın; başka bir sunucunun
bellek içi kimliklerini değil. PhotoCraft, DesignCraft için PNG; DesignCraft,
PdfCraft için PDF dışa aktarabilir. Bir aşama başarısız olursa son doğrulanmış
yapıtta durun. Evrensel toplu işlem, otomatik yazma yinelemesi ya da gizli
yedek yol vaat edilmez.

Üç uygulamanın kaynakta belgelenmiş ayrı okuma/yazma kökleri vardır;
PdfCraft'ın tek kökü vardır; sekiz uygulama işletim sistemi kullanıcısı
genelinde erişime sahip kabul edilmelidir. Ne Skill, ne yoklama makbuzları, ne
de MCP yapılandırması bir işletim sistemi sanal alanıdır. Host'un diğer
kabuk/dosya araçları da uygun izinlere ihtiyaç duyar. Bkz.
[güvenlik](SECURITY.md).

## Depo haritası

| Yol | Sorumluluk |
|---|---|
| `skills/craft/` | Tek yönlendirici Skill, on iki uygulama kartı ve iki iş akışı |
| `config/` | Gözden geçirilmiş başlatma kataloğu, sürüm manifesti ve Sigstore paket deposu, pasif şablonlar, örnek kilit/ortam |
| `storytold_tools/`, `storytold.py` | Deterministik CLI ve isteğe bağlı kısa ömürlü SDK yoklaması |
| `scripts/`, `Makefile` | Çevrimdışı denetimler, testler, korumalı derlemeler ve paketleme |
| `tests/` | Çekirdek regresyon testleri, sentetik SDK fikstürü, yerel kabul senaryoları |
| `docs/` | Mimari, işletim, güvenlik sınırları, kaynaklar ve doğrulama |
| `plugins/storytold/` | Üretilen ortak çalışma zamanı; asla ayrıca düzenlemeyin |
| `.github/workflows/` | Çevrimdışı CI matrisi ile günlük sürüm yenileme, imzalama ve üç işletim sisteminde doğrulama |

[Mimari](docs/architecture.md), yerel planın neden eski ağ geçidi
referansından önce geldiğini ve hangi bileşenin neye sahip olduğunu kayda geçirir.

Devsolux entegrasyonudur; upstream `storytold` organizasyonu, Anthropic ya da
OpenAI ile bir bağlılık ya da onay iddia edilmez.
[MIT Lisansı](LICENSE) ile yayımlanmıştır. Yerel uygulamalar, SDK'lar, yazı
tipleri ve medya pakete dahil değildir ve kendi lisanslarını korur; bkz.
[lisans bildirimi](LICENSE-NOTICE.md).
