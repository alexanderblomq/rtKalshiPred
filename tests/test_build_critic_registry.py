from pipelines.build_critic_registry import (
    build_letter_urls,
    merge_publications,
    parse_critics_html,
    parse_publications_html,
    parse_top_critics_html,
)


def test_build_letter_urls_covers_hash_and_alphabet():
    urls = build_letter_urls("https://www.rottentomatoes.com/critics/authors")
    assert urls[0] == "https://www.rottentomatoes.com/critics/authors?letter=%23"
    assert urls[1] == "https://www.rottentomatoes.com/critics/authors?letter=a"
    assert urls[-1] == "https://www.rottentomatoes.com/critics/authors?letter=z"
    assert len(urls) == 27


def test_parse_publications_html_extracts_publication_entries():
    html = """
    <ul>
      <li class="critics__list-item" data-qa="publication-item">
        <p>
          <a class="critic-publication__name a" href="/critics/source/2401" data-qa="publication-item-link">AARP Movies for Grownups</a>
          <span class="critic-authors__publication">
            <rt-badge>Approved publication</rt-badge>
          </span>
        </p>
      </li>
    </ul>
    """
    entries = parse_publications_html(html)
    assert len(entries) == 1
    assert entries[0]["publication_id"] == "aarp_movies_for_grownups"
    assert entries[0]["approved_publication"] is True


def test_parse_critics_html_extracts_critic_and_publication():
    html = """
    <ul>
      <li class="critics__list-item" data-qa="critic-item">
        <p>
          <a class="critic-authors__name" href="/critics/ganesh-aaglave" data-qa="critic-item-link">Ganesh Aaglave</a>
          <span>when published by <a class="critic-authors__publication a" href="/critics/source/2784" data-qa="critic-item-publication-link">Firstpost</a></span>
        </p>
      </li>
      <li class="critics__list-item" data-qa="critic-item">
        <p>
          <a class="critic-authors__name" href="/critics/mae-abdulbaki" data-qa="critic-item-link">Mae Abdulbaki</a>
          <span><rt-badge>Individually approved</rt-badge></span>
        </p>
      </li>
    </ul>
    """
    entries = parse_critics_html(html)
    assert len(entries) == 2
    assert entries[0]["publication_id"] == "firstpost"
    assert entries[0]["approval_type"] == "publication_bound"
    assert entries[1]["approval_type"] == "individually_approved"


def test_parse_top_critics_html_extracts_critic_ids():
    html = """
    <ul>
      <li class="critics__list-item" data-qa="critic-item">
        <a class="critic-authors__name" href="/critics/richard-brody" data-qa="critic-item-link">Richard Brody</a>
      </li>
    </ul>
    """
    critic_ids = parse_top_critics_html(html)
    assert "richard-brody" in critic_ids


def test_merge_publications_preserves_manual_settings_and_adds_critic_names():
    existing = [
        {
            "publication_id": "newyorker",
            "outlet_name": "The New Yorker",
            "approved_publication": True,
            "source_type": "article",
            "enabled": True,
            "critic_names": ["Richard Brody"],
            "site_base_url": "https://www.newyorker.com",
            "adapter": "article",
        }
    ]
    discovered = [
        {
            "publication_id": "newyorker",
            "outlet_name": "The New Yorker",
            "approved_publication": True,
            "source_type": "article",
            "enabled": False,
            "critic_names": [],
            "site_base_url": None,
            "adapter": "article",
            "rt_source_path": "/critics/source/9999",
            "rt_badge": "Approved publication",
        }
    ]
    critics = [
        {
            "critic_id": "richard-brody",
            "critic_name": "Richard Brody",
            "publication_name": "The New Yorker",
            "publication_id": "newyorker",
        },
        {
            "critic_id": "justin-chang",
            "critic_name": "Justin Chang",
            "publication_name": "The New Yorker",
            "publication_id": "newyorker",
        },
    ]

    merged = merge_publications(existing, discovered, critics)
    assert len(merged) == 1
    assert merged[0]["enabled"] is True
    assert merged[0]["site_base_url"] == "https://www.newyorker.com"
    assert merged[0]["critic_names"] == ["Justin Chang", "Richard Brody"]
