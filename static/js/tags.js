var negrelnames = new Bloodhound({
  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
  queryTokenizer: Bloodhound.tokenizers.whitespace,
  prefetch: {
    url: 'static/js/json/relnames.json',
    filter: function(list) {
      return $.map(list, function(negrelname) {
        return { name: negrelname }; });
    }
  }
});
negrelnames.initialize();

$('#negrels').val("circ");

$('#negrels').tagsinput({
  typeaheadjs: {
    name: 'negrelnames',
    displayKey: 'name',
    valueKey: 'name',
    source: negrelnames.ttAdapter()
  }
});
