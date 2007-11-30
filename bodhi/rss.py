# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

from turbogears.feed import FeedController
from turbogears import expose, config, url
from sqlobject.sqlbuilder import AND

from bodhi.model import Release, PackageUpdate

class Feed(FeedController):

    def get_feed_data(self, release=None, type=None, status=None, *args, **kw):
        query = []
        entries = []
        date = lambda update: update.date_pushed
        order = PackageUpdate.q.date_pushed
        title = []

        if release:
            rel = Release.byName(release.upper())
            query.append(PackageUpdate.q.releaseID == rel.id)
            title.append(rel.long_name)
        if type:
            query.append(PackageUpdate.q.type == type)
            title.append(type.title())
        if status:
            query.append(PackageUpdate.q.status == status)
            if status == 'pending':
                date = lambda update: update.date_submitted
                order = PackageUpdate.q.date_submitted
            else:
                # Let's only show pushed testing/stable updates
                query.append(PackageUpdate.q.pushed == True)
            title.append(status.title())
        else:
            query.append(PackageUpdate.q.pushed == True)

        updates = PackageUpdate.select(AND(*query), orderBy=order).reversed()[:20]

        for update in updates:
            entries.append({
                'id'        : config.get('base_address') + url(update.get_url()),
                'summary'   : update.notes,
                'published' : date(update),
                'link'      : config.get('base_address') + url(update.get_url()),
                'title'     : "%s %sUpdate: %s" % (update.release.long_name,
                                                   update.type == 'security'
                                                   and 'Security ' or '',
                                                   update.title)
            })
            if len(update.bugs):
                bugs = "<b>Resolved Bugs</b><br/>"
                for bug in update.bugs:
                    bugs += "<a href=%s>%d</a> - %s<br/>" % (bug.get_url(),
                                                             bug.bz_id, bug.title)
                entries[-1]['summary'] = "%s<br/>%s" % (bugs[:-2],
                                                        entries[-1]['summary'])

        title.append('Updates')

        return dict(
                title = ' '.join(title),
                subtitle = "",
                link = config.get('base_address') + url('/'),
                entries = entries
        )
